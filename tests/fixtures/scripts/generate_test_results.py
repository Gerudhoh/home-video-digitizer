# 100% vibe coded by Claude Code

import html
import json
import statistics
import sys
from pathlib import Path

DEFAULT_OUTPUT = "results.html"

# Per issues/plans/002-transcript-testing.md: pass threshold is 0.85 (0-1 scale).
PASS_THRESHOLD = 0.85
WARN_THRESHOLD = 0.4


def normalize_entry(entry):
    if isinstance(entry, (int, float)):
        return {"score": entry, "comments": [], "parse_error": None}

    if isinstance(entry, dict) and "score" in entry:
        return {
            "score": entry["score"],
            "comments": entry.get("comments", []),
            "parse_error": None,
        }

    return {
        "score": None,
        "comments": [],
        "parse_error": f"unrecognized entry: {entry!r}",
    }


def score_band(score):
    if score is None:
        return "error"
    if score >= PASS_THRESHOLD:
        return "pass"
    if score >= WARN_THRESHOLD:
        return "warn"
    return "fail"


def render_html(results):
    scored = [r["score"] for r in results if r["score"] is not None]
    mean = statistics.fmean(scored) if scored else None
    spread = statistics.pstdev(scored) if len(scored) > 1 else 0.0
    parse_failures = sum(1 for r in results if r["parse_error"])

    rows = []
    for i, r in enumerate(results, start=1):
        band = score_band(r["score"])
        score_display = f"{r['score']:.2f}" if r["score"] is not None else "N/A"
        comments_html = (
            "<ul>"
            + "".join(f"<li>{html.escape(c)}</li>" for c in r["comments"])
            + "</ul>"
            if r["comments"]
            else "<em>none</em>"
        )
        error_html = (
            f'<div class="parse-error">{html.escape(r["parse_error"])}</div>'
            if r["parse_error"]
            else ""
        )
        rows.append(f"""
        <tr class="{band}">
          <td>{i}</td>
          <td class="score">{score_display}</td>
          <td>{comments_html}{error_html}</td>
        </tr>
        """)

    summary_html = f"""
    <ul class="summary">
      <li>Runs: {len(results)}</li>
      <li>Parse failures: {parse_failures}</li>
      <li>Mean score: {f"{mean:.2f}" if mean is not None else "N/A"}</li>
      <li>Score spread (stdev): {spread:.2f}</li>
    </ul>
    """

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Whisper Validation Results</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }}
  h1 {{ font-size: 1.4rem; }}
  .summary {{ list-style: none; padding: 0; display: flex; gap: 1.5rem; font-weight: 600; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1.5rem; }}
  th, td {{ border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; vertical-align: top; }}
  th {{ background: #f5f5f5; }}
  tr.pass {{ background: #eaf7ea; }}
  tr.warn {{ background: #fff8e1; }}
  tr.fail {{ background: #fdeaea; }}
  tr.error {{ background: #eee; }}
  .score {{ font-weight: 700; }}
  .parse-error {{ color: #b00; font-size: 0.85rem; margin-top: 0.25rem; }}
  ul {{ margin: 0; padding-left: 1.2rem; }}
</style>
</head>
<body>
  <h1>Whisper Validation Results</h1>
  {summary_html}
  <table>
    <thead>
      <tr><th>#</th><th>Score</th><th>Comments</th></tr>
    </thead>
    <tbody>
      {"".join(rows)}
    </tbody>
  </table>
</body>
</html>
"""


def generate_test_results_file(scores_path, output_path):
    entries = json.loads(scores_path.read_text(encoding="utf-8"))
    results = [normalize_entry(e) for e in entries]

    output_path.write_text(render_html(results), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            f"Usage: generate_test_results.py <scores_json_path> [output_html={DEFAULT_OUTPUT}]"
        )
        sys.exit(1)

    scores_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(DEFAULT_OUTPUT)

    generate_test_results_file(scores_path, output_path)
