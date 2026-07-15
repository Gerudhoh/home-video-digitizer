import json
import sys
import os
import requests
import ffmpeg
import smbclient
import smbclient.shutil

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
        ffmpeg.run(output, overwrite_output=True)
    except ffmpeg.Error as e:
        raise RuntimeError(
            f"ffmpeg audio extraction failed: {e.stderr.decode('utf-8')}"
        ) from e

    return audio_track_path


def mount_audio_file_to_server(audio_track_path):
    remote_path = rf"\\{SAMBA_HOST}\Share\TapeAudio\{audio_track_path.name}"
    smbclient.shutil.copy(str(audio_track_path), remote_path)
    # Return the SMB path (for cleanup) and the path as the whisper container sees the same volume
    return remote_path, f"{WHISPER_SHARE_ROOT}/TapeAudio/{audio_track_path.name}"


def transcribe(server_audio_path: Path):
    resp = requests.post(
        f"{WHISPER_HOST}/transcribe",
        json={
            "input_path": str(server_audio_path),
        },
        timeout=300,
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


if __name__ == "__main__":
    result = get_json_transcription(Path(sys.argv[1]))
    print(json.dumps(result, indent=2, ensure_ascii=False))
