from pathlib import Path

import pytest

from ffmpeg_helper import FfmpegHelper

FIXTURES_DIR = Path(__file__).parent.parent
SCENE_SPLIT_FIXTURES = FIXTURES_DIR / "raw" / "christian" / "scene_split"

# Detector params pinned here rather than read from ffmpeg_helper.py's defaults, so a
# future tuning change there becomes a deliberate edit to these tests instead of
# silently redefining what they measure.
ADAPTIVE_THRESHOLD = 5.0
WINDOW_WIDTH = 3
MIN_SCENE_LEN = 30


def _detect(fixture_name):
    path = SCENE_SPLIT_FIXTURES / fixture_name
    if not path.exists():
        pytest.skip(
            f"fixture not present: {path}; run "
            "tests/fixtures/scripts/make_scene_split_fixtures.py to regenerate it "
            "from the source tape"
        )
    return FfmpegHelper.get_scene_bounds(
        path,
        threshold=ADAPTIVE_THRESHOLD,
        window_width=WINDOW_WIDTH,
        min_scene_len=MIN_SCENE_LEN,
    )


def test_normal_clip_boundary_produces_clean_split():
    """#12 task: 'A normal clip boundary produces a clean split'.

    clean_cut.mp4 is a 33s clip trimmed around 00:09:53-00:10:26 of
    test-tape-screen-split.mp4, containing exactly one real, isolated cut
    (adaptive_ratio 7.8 at 00:10:09.833, next-highest score in the clip is 2.8).
    """
    scenes = _detect("clean_cut.mp4")
    assert len(scenes) == 2


def test_calm_segment_is_not_split():
    """#12 task: 'Silence/low-narration segment is NOT incorrectly split'.

    no_cut_calm.mp4 is a 40s clip trimmed from a stable, uneventful stretch
    (00:06:00-00:06:40) with no real cuts (max adaptive_ratio observed there is
    3.05, well under threshold). get_scene_bounds() returns an empty list, not a
    single whole-clip scene, when PySceneDetect finds no cut points.
    """
    scenes = _detect("no_cut_calm.mp4")
    assert len(scenes) == 0


@pytest.mark.xfail(
    reason=(
        "Known false positive, not yet resolved by detector tuning: a fast zoom around "
        "00:05:12-00:05:18 in the source tape produces two spurious cuts "
        "(adaptive_ratio 6.57 and 5.69) that clear adaptive_threshold=5.0 because the "
        "content-value spike there is real and isolated, not smoothed out by "
        "window_width the way a gradual pan would be. Revisit this test if "
        "ADAPTIVE_THRESHOLD/WINDOW_WIDTH above change, or if a fix narrows detection to "
        "sustained motion specifically."
    ),
    strict=True,
)
def test_zoom_is_not_incorrectly_split():
    scenes = _detect("zoom_false_positive.mp4")
    assert len(scenes) == 0
