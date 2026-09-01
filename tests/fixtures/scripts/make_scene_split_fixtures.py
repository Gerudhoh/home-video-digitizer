"""Regenerates tests/fixtures/raw/christian/scene_split/*.mp4.

These are short, re-encoded clips trimmed out of
tests/fixtures/raw/christian/test-tape-screen-split.mp4 (the ~991MB, gitignored
source tape) around three known events, found by inspecting PySceneDetect's
StatsManager CSV output against that source at
adaptive_threshold=5.0, window_width=3, min_scene_len=30
(see tests/fixtures/tests/test_scene_split.py for the params these fixtures are
meant to be exercised with).

Re-encoding (rather than `-c copy`) matters here: stream-copy trims snap to the
nearest keyframe, so the clip's actual start drifts from the requested -ss and
every timestamp expectation below would silently be wrong.

Run from the repo root:
    python tests/fixtures/scripts/make_scene_split_fixtures.py
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
SRC = REPO_ROOT / "tests/fixtures/raw/christian/test-tape-screen-split.mp4"
OUT_DIR = REPO_ROOT / "tests/fixtures/raw/christian/scene_split"

# (output filename, start timecode, duration seconds, what it's for)
CLIPS = [
    (
        "clean_cut.mp4",
        "00:10:04.833",
        10,
        "one isolated real cut at 00:10:09.833 (adaptive_ratio 7.8) -> 2 scenes",
    ),
    (
        "no_cut_calm.mp4",
        "00:06:15.000",
        10,
        "stable stretch, max adaptive_ratio observed ~3.05 (< threshold) -> 0 scenes",
    ),
    (
        "zoom_false_positive.mp4",
        "00:05:10.967",
        9.2,
        "known false positive: fast zoom spikes at 00:05:12.967 (ratio 6.57) and "
        "00:05:18.167 (ratio 5.69) -> 3 scenes (2 spurious cuts)",
    ),
]


def main():
    if not SRC.exists():
        raise SystemExit(f"source tape not found: {SRC}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename, start, duration, note in CLIPS:
        out_path = OUT_DIR / filename
        print(f"{filename}: {note}")
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", start,
                "-i", str(SRC),
                "-t", str(duration),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac",
                str(out_path),
                "-loglevel", "error",
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
