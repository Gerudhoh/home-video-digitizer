import json
import sys
import os
import requests
import ffmpeg
import smbclient
import smbclient.shutil
from Scene import SceneMetaData

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WHISPER_HOST = os.environ["WHISPER_HOST"]
SAMBA_HOST = os.environ["SAMBA_HOST"]
SAMBA_USERNAME = os.environ["SAMBA_USERNAME"]
SAMBA_PASSWORD = os.environ["SAMBA_PASSWORD"]
WHISPER_SHARE_ROOT = "/media/library"  # where the whisper CT mounts the shared volume

smbclient.ClientConfig(username=SAMBA_USERNAME, password=SAMBA_PASSWORD)


def create_audio_path(video_path):
    audio_dir = Path(
        *["audio" if part == "raw" else part for part in video_path.parent.parts]
    )
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_track_path = audio_dir / video_path.with_suffix(".mp3").name
    stream = ffmpeg.input(video_path)
    audio = stream.audio
    output = ffmpeg.output(audio, str(audio_track_path), acodec="libmp3lame")
    try:
        ffmpeg.run(output, overwrite_output=True, capture_stderr=True)
    except ffmpeg.Error as e:
        raise RuntimeError(
            f"ffmpeg audio extraction failed: {e.stderr.decode('utf-8')}"
        ) from e

    return audio_track_path


def mount_audio_file_to_server(audio_track_path):
    owner = audio_track_path.parent.name
    remote_dir = rf"\\{SAMBA_HOST}\Share\TapeAudio\{owner}"
    smbclient.makedirs(remote_dir, exist_ok=True)
    remote_path = rf"{remote_dir}\{audio_track_path.name}"
    smbclient.shutil.copy(str(audio_track_path), remote_path)
    # Return the SMB path (for cleanup) and the path as the whisper container sees the same volume
    return remote_path, f"{WHISPER_SHARE_ROOT}/TapeAudio/{owner}/{audio_track_path.name}"


# Vocabulary hint passed to Whisper via initial_prompt to bias decoding toward
# these spellings -- without it, proper names get misheard into phonetically
# plausible nonsense (e.g. "Kath" -> "Cat", "Paula" -> "hall"). Hardcoded here as
# a stopgap; move into the planned shared people/dates config (issue #9) once it
# exists, since the actual names differ per household.
NAME_VOCABULARY_PROMPT = "Kath, Julia, Pete, Annie, Ben, Jess, Bobo, Paula, Christian"


def transcribe(server_audio_path: Path):
    resp = requests.post(
        f"{WHISPER_HOST}/transcribe",
        json={
            "input_path": str(server_audio_path),
            "initial_prompt": NAME_VOCABULARY_PROMPT,
        },
    )
    resp.raise_for_status()
    result = resp.json()

    return {
        "language": result["language"],
        "duration": result["duration"],
        "text": result["text"],
    }


def get_json_transcription(video_path):
    audio_track_path = create_audio_path(video_path)
    try:
        remote_path, server_audio_path = mount_audio_file_to_server(audio_track_path)
        try:
            return transcribe(server_audio_path)
        finally:
            smbclient.remove(remote_path)
    finally:
        audio_track_path.unlink(missing_ok=True)


def create_transcript_path(video_path):
    transcript_dir = Path(
        *["transcripts" if part == "raw" else part for part in video_path.parent.parts]
    )
    return transcript_dir / video_path.with_suffix(".json").name

def write_scene_trancript(scene):
    return write_transcript(scene.video_path, scene.transcript)

def write_transcript(video_path, transcript_json=None):
    output_path = create_transcript_path(video_path)
    if output_path.exists() and not force:
            print(f"Skipping {video_path}: transcript already exists at {output_path} (use --force to re-run)")
            return None
    
    result = transcript_json or get_json_transcription(video_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = len(args) != len(sys.argv[1:])
    video_path = Path(args[0])
    write_transcript(video_path)
