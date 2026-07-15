import json
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent

sys.path.insert(0, str(FIXTURES_DIR / "scripts"))

from validate_whisper import validate_via_llm
from generate_test_results import generate_test_results_file

test_transcripts = [
    {
        "golden": str(FIXTURES_DIR / "transcripts/julia/tape001_2026-07-13_GOLDEN.txt"),
        "generated": str(FIXTURES_DIR / "transcripts/julia/tape001_2026-07-13.json"),
    },
    {
        "golden": str(FIXTURES_DIR / "transcripts/julia/tape002_2026-07-15_GOLDEN.txt"),
        "generated": str(FIXTURES_DIR / "transcripts/julia/tape002_2026-07-15.json"),
    },
    {
        "golden": str(FIXTURES_DIR / "transcripts/julia/tape003_2026-07-15_GOLDEN.txt"),
        "generated": str(FIXTURES_DIR / "transcripts/julia/tape003_2026-07-15.json"),
    },
]


def extract_judgement(raw_response):
    try:
        return json.loads(raw_response["response"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return raw_response


if __name__ == "__main__":
    results = []
    for transcript in test_transcripts:
        try:
            raw_response = validate_via_llm(transcript["generated"], transcript["golden"])
            results.append(extract_judgement(raw_response))
        except Exception as e:
            results.append({"judge_call_failed": f"{transcript['generated']}: {e}"})
    results_path = FIXTURES_DIR / "results.json"
    results_path.write_text(json.dumps(results, indent=4), encoding="utf-8")
    generate_test_results_file(results_path, FIXTURES_DIR / "results.html")
