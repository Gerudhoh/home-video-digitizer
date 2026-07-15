# Plan: Issue #2 — Transcripts: Testing

Source: https://github.com/Gerudhoh/home-video-digitizer/issues/2
Depends on: #3 (closed — local Whisper set up in `.venv-whisper`)

> **Implementation status:** this plan predates the code and hasn't been kept in sync. What's actually under `tests/fixtures/{prompts,scripts,tests}/` diverges from the plan below in several ways:
> - Goldens live next to their transcripts in `tests/fixtures/transcripts/<owner>/` as `_GOLDEN.txt` files, not in a separate `tests/fixtures/goldens/` dir (the plan's stated reason for the split — never diffing a golden against itself — doesn't apply since the two use different filenames).
> - No shared `config.py`/`.toml`: `JUDGE_MODEL` (`llama3.1:8b`) is hardcoded in `validate_whisper.py`; there's no `JUDGE_TEMPERATURE`, `JUDGE_SAMPLES_PER_FIXTURE`, or `JUDGE_PASS_THRESHOLD` anywhere in the codebase.
> - The judge runs once per fixture (not 3x + median), score is 0–1 not 0–100, and nothing enforces a pass/fail threshold — `whisper_tests.py` just writes every raw score into `results.json`/`results.html` for a human to read.
> - `generate_test_results.py`'s HTML report (pass ≥0.7 / warn ≥0.4 / fail below, per-run color bands) isn't described in this plan at all.
> - The runner is `tests/fixtures/tests/whisper_tests.py`, not `tests/test_transcripts.py`.
> The "Decisions" and "Pseudocode" sections below are kept as the historical record of what was originally intended; treat the code as authoritative for what's actually running.

## Decisions

- **Comparison method: LLM-as-judge**, calling the Ollama instance on the homelab server (bespin LXC) over its HTTP API — not a locally-installed model on the dev machine.
  - More forgiving than WER on rephrasing, filler words, and transcription of unclear toddler speech — appropriate since goldens are hand-written prose, not a word-for-word script Whisper is expected to match exactly.
  - Tradeoff accepted: non-deterministic (a re-run can nudge a borderline score) and requires the bespin Ollama instance to be reachable — the test can't run fully offline/on a plane. Mitigated by setting `temperature=0` on the judge call and treating a judge score at/near the threshold as worth a manual look rather than pure automation.
  - Judge prompt gives the model both texts (golden + Whisper output) and asks it to return a single numeric semantic-similarity/accuracy score in a fixed range (e.g. 0-100) plus a one-line rationale, not free-form commentary — the rationale is for a human skimming failures, not parsed by the script.
- **Pass threshold: judge score >= 85 per fixture** (tunable constant in one shared config location, not hardcoded inline).
  - Starting point; revisit once all 3 fixtures are run for real and we see how the judge scores actual Whisper output on this hardware/model size.
  - Because the judge is non-deterministic, the runner calls it a fixed small number of times (e.g. 3) per fixture and uses the median score against the threshold, rather than a single call, to reduce flakiness.
- Existing `tape001` clip + hand-written `.txt` golden count as fixture 1 (multi-speaker dialogue). Fixtures 2 (sparse/quiet dialogue) and 3 (toddler babbling) still need to be captured/added.

## File structure

```
tests/
  fixtures/
    raw/
      julia/
        tape001_2026-07-13.mp4        # existing — multi-speaker dialogue
        tape002_2026-07-13.mp4        # new — sparse/quiet dialogue
        tape003_2026-07-13.mp4        # new — toddler babbling
    goldens/
      julia/
        tape001_2026-07-13.txt        # hand-written expected transcript (plain text, one utterance per line)
        tape002_2026-07-13.txt
        tape003_2026-07-13.txt
    transcripts/
      julia/
        tape001_2026-07-13.json       # Whisper output (regenerated each test run, gitignored or overwritten)
        tape002_2026-07-13.json
        tape003_2026-07-13.json
  test_transcripts.py                  # new — the test runner described below

scripts/
  transcribe.py                        # existing — unchanged, reused as a library function
```

Note: this moves the hand-written golden `.txt` files out of `tests/fixtures/transcripts/` (which should hold only Whisper's *actual* output) and into a sibling `tests/fixtures/goldens/` dir, so "expected" and "actual" are never in the same folder under the same naming pattern — avoids accidentally diffing a golden against itself or overwriting a golden with fresh Whisper output.

## Pseudocode

### 1. Shared config (thresholds + judge connection live in one place per CLAUDE.md's cross-cutting concerns note)

```
# tests/fixtures/config.py (or .toml)
OLLAMA_HOST = "http://bespin.local:11434"   # or whatever hostname/IP the LXC resolves to
JUDGE_MODEL = "llama3.1"                    # whichever model is pulled on bespin for this purpose
JUDGE_TEMPERATURE = 0
JUDGE_SAMPLES_PER_FIXTURE = 3
JUDGE_PASS_THRESHOLD = 85                   # 0-100 scale, median of JUDGE_SAMPLES_PER_FIXTURE calls
FIXTURES = [
    { owner: "julia", tape_id: "tape001", date: "2026-07-13", label: "multi-speaker dialogue" },
    { owner: "julia", tape_id: "tape002", date: "2026-07-13", label: "sparse/quiet dialogue" },
    { owner: "julia", tape_id: "tape003", date: "2026-07-13", label: "toddler babbling" },
]
```

### 2. Golden loader

```
function load_golden(owner, tape_id, date):
    path = tests/fixtures/goldens/{owner}/{tape_id}_{date}.txt
    lines = read_lines(path)
    lines = [line for line in lines if line is not blank]   # golden .txt has blank separator lines
    return join(lines, " ")
```

### 3. Whisper runner (reuses existing scripts/transcribe.py)

```
function run_whisper(owner, tape_id, date):
    video_path = tests/fixtures/raw/{owner}/{tape_id}_{date}.mp4
    result = transcribe(video_path)   # from scripts/transcribe.py

    out_path = tests/fixtures/transcripts/{owner}/{tape_id}_{date}.json
    write_json(out_path, result)

    full_text = join([seg.text for seg in result.segments], " ")
    return full_text
```

### 4. Judge prompt + single call to bespin Ollama

```
JUDGE_PROMPT_TEMPLATE = """
You are grading a speech-to-text transcript against a hand-written reference transcript
of the same short home-video clip. Score how well the CANDIDATE captures the same content,
speakers, and meaning as the REFERENCE, on a 0-100 scale (100 = fully equivalent in meaning,
allowing for reasonable rephrasing; 0 = unrelated).

REFERENCE:
{golden_text}

CANDIDATE:
{actual_text}

Respond with exactly two lines:
SCORE: <integer 0-100>
REASON: <one sentence>
"""

function call_judge(golden_text, actual_text):
    prompt = JUDGE_PROMPT_TEMPLATE.format(golden_text, actual_text)

    response = http_post(f"{OLLAMA_HOST}/api/generate", {
        model: JUDGE_MODEL,
        prompt: prompt,
        temperature: JUDGE_TEMPERATURE,
        stream: false,
    })

    score = parse_int(extract_line(response.text, prefix="SCORE:"))
    reason = extract_line(response.text, prefix="REASON:")
    return { score: score, reason: reason }
```

### 5. Scoring (median of several judge calls, per fixture)

```
function score_fixture(fixture):
    golden_text = load_golden(fixture.owner, fixture.tape_id, fixture.date)
    actual_text = run_whisper(fixture.owner, fixture.tape_id, fixture.date)

    judgements = [call_judge(golden_text, actual_text) for _ in range(JUDGE_SAMPLES_PER_FIXTURE)]
    median_score = median([j.score for j in judgements])
    passed = median_score >= JUDGE_PASS_THRESHOLD

    return {
        fixture: fixture.label,
        score: median_score,
        passed: passed,
        reasons: [j.reason for j in judgements],   # kept for a human to skim on failure
    }
```

### 6. Test runner / report (the acceptance-criteria deliverable)

```
function main():
    assert_ollama_reachable(OLLAMA_HOST)   # fail fast with a clear error, not a confusing timeout mid-run

    results = [score_fixture(f) for f in FIXTURES]

    for r in results:
        print(f"{r.fixture}: score={r.score} threshold={JUDGE_PASS_THRESHOLD} -> {'PASS' if r.passed else 'FAIL'}")
        if not r.passed:
            for reason in r.reasons:
                print(f"    - {reason}")

    if all(r.passed for r in results):
        exit(0)
    else:
        exit(1)   # nonzero exit so this plugs into CI / a pre-commit-style check later
```

### 7. Idempotency note

Whisper is re-run every invocation (transcription is the thing under test, not something to skip), but the *output* is always written to a fixed, predictable path — no timestamped output files piling up. This differs from the pipeline's own idempotency rule (skip if already processed), which applies to production stages, not to this test harness.

## Open items / blockers before this can be run end-to-end

1. Fixture 2 (sparse/quiet dialogue) and fixture 3 (toddler babbling) clips don't exist yet — need to be captured/trimmed from real tapes and added under `tests/fixtures/raw/julia/`.
2. Hand-written goldens for those two fixtures still need to be written.
3. Need to confirm: the actual bespin hostname/IP and port for Ollama, and which model is pulled there for judging (vs. whatever's used for production tagging) — placeholder values used above.
4. Need an HTTP client available in the whisper venv to call the Ollama `/api/generate` endpoint (most Python HTTP libraries work; no new service dependency beyond reaching bespin over the network) — no `requirements.txt`/`pyproject.toml` exists in the repo yet to record this.
5. Test run now has a hard runtime dependency on bespin being powered on and reachable from wherever the test executes (dev machine vs. CI) — worth deciding if that's acceptable or if a "skip if unreachable" mode is needed later.
6. Existing `tests/fixtures/transcripts/julia/tape001_2026-07-13.txt` should be moved to `tests/fixtures/goldens/julia/tape001_2026-07-13.txt` under the new structure above.

## Downstream reuse

This fixture set (`tests/fixtures/raw/` + `goldens/`) is reused as-is by #12/#13/#14 per the issue — those stages should read the same raw clips rather than capturing their own.
