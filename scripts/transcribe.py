import json
import sys
from pathlib import Path

from faster_whisper import WhisperModel


def transcribe(video_path: Path, model_size: str = "small"):
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(
        str(video_path),
        beam_size=5,
        vad_filter=False,
        no_speech_threshold=0.1,
        log_prob_threshold=-2.0,
        condition_on_previous_text=False,
        word_timestamps=True,
    )

    return audio_track_path


def mount_audio_file_to_server(audio_track_path):
    owner = audio_track_path.parent.name
    remote_dir = rf"\\{SAMBA_HOST}\Share\TapeAudio\{owner}"
    smbclient.makedirs(remote_dir, exist_ok=True)
    remote_path = rf"{remote_dir}\{audio_track_path.name}"
    smbclient.shutil.copy(str(audio_track_path), remote_path)
    # Return the SMB path (for cleanup) and the path as the whisper container sees the same volume
    return remote_path, f"{WHISPER_SHARE_ROOT}/TapeAudio/{owner}/{audio_track_path.name}"


def transcribe(server_audio_path: Path):
    resp = requests.post(
        f"{WHISPER_HOST}/transcribe",
        json={
            "input_path": str(server_audio_path),
        },
    )
    resp.raise_for_status()
    result = resp.json()

    return {
        "language": result["language"],
        "duration": result["duration"],
        "text": result["text"],
    }
    return result


if __name__ == "__main__":
    video_path = Path(sys.argv[1])
    result = transcribe(video_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
