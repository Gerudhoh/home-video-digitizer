import json
import os
from pathlib import Path

import pytest
import requests

from generate_test_results import PASS_THRESHOLD
from validate_whisper import validate_via_llm

FIXTURES_DIR = Path(__file__).parent.parent

TRANSCRIPTS = [
    pytest.param(
        FIXTURES_DIR / "transcripts/julia/tape001_2026-07-13.json",
        FIXTURES_DIR / "transcripts/julia/tape001_2026-07-13_GOLDEN.txt",
        id="tape001",
    ),
    pytest.param(
        FIXTURES_DIR / "transcripts/julia/tape002_2026-07-15.json",
        FIXTURES_DIR / "transcripts/julia/tape002_2026-07-15_GOLDEN.txt",
        id="tape002",
    ),
    pytest.param(
        FIXTURES_DIR / "transcripts/julia/tape003_2026-07-15.json",
        FIXTURES_DIR / "transcripts/julia/tape003_2026-07-15_GOLDEN.txt",
        id="tape003",
    ),
]


@pytest.mark.quality
@pytest.mark.skipif(not os.environ.get("OLLAMA_HOST"), reason="OLLAMA_HOST not set")
@pytest.mark.parametrize("generated, golden", TRANSCRIPTS)
def test_whisper_transcript_matches_golden(generated, golden):
    try:
        raw_response = validate_via_llm(str(generated), str(golden))
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Ollama judge unreachable: {e}")

    try:
        judgement = json.loads(raw_response["response"])
    except (KeyError, TypeError, json.JSONDecodeError) as e:
        pytest.fail(f"judge returned an unparsable response: {raw_response!r} ({e})")

    score = judgement.get("score")
    comments = judgement.get("comments", [])
    assert score is not None, f"judge response missing 'score': {judgement!r}"
    assert score >= PASS_THRESHOLD, (
        f"score {score:.2f} below pass threshold {PASS_THRESHOLD}; comments: {comments}"
    )
