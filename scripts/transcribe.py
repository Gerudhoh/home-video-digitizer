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

    result = {
        "language": info.language,
        "duration": info.duration,
        "segments": [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "words": [
                    {"start": w.start, "end": w.end, "word": w.word}
                    for w in (seg.words or [])
                ],
            }
            for seg in segments
        ],
    }
    return result


if __name__ == "__main__":
    video_path = Path(sys.argv[1])
    result = transcribe(video_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
