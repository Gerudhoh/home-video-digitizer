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
    audio_dir = Path(*["audio" if part == "raw" else part for part in video_path.parent.parts])
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_track_path = audio_dir / video_path.with_suffix(".mp3").name
    stream = ffmpeg.input(video_path)
    audio = stream.audio
    output = ffmpeg.output(audio, str(audio_track_path), acodec="libmp3lame")
    try:
        ffmpeg.run(output, overwrite_output=True)
    except ffmpeg.Error as e:
        raise RuntimeError(f"ffmpeg audio extraction failed: {e.stderr.decode('utf-8')}") from e

    return audio_track_path

def mount_audio_file_to_server(audio_track_path):
    remote_path = rf"\\{SAMBA_HOST}\Share\TapeAudio\{audio_track_path.name}"
    smbclient.shutil.copy(str(audio_track_path), remote_path)
    # Return the path as the whisper container sees the same volume
    return f"{WHISPER_SHARE_ROOT}/TapeAudio/{audio_track_path.name}"

def transcribe(server_audio_path: Path):
    resp = requests.post(
        f"{WHISPER_HOST}/transcribe",
        json={
            "input_path": str(server_audio_path),
        },
    )
    result = resp.json()
    print(result)

    # result = {
    #     "language": info.language,
    #     "duration": info.duration,
    #     "segments": [
    #         {
    #             "start": seg.start,
    #             "end": seg.end,
    #             "text": seg.text.strip(),
    #             "words": [
    #                 {"start": w.start, "end": w.end, "word": w.word}
    #                 for w in (seg.words or [])
    #             ],
    #         }
    #         for seg in segments
    #     ],
    # }
    # return result


if __name__ == "__main__":
    video_path = Path(sys.argv[1])
    audio_track_path = create_audio_path(video_path)
    sever_audio_path = mount_audio_file_to_server(audio_track_path)
    result = transcribe(sever_audio_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
