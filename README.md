# home-video-digitizer

Scripts to digitize, organize, tag, split, and share home videos — turning old camcorder/VHS tapes into a searchable, tagged library hosted on Jellyfin.

## Planned pipeline

1. **Capture/digitize** raw tapes into video files, using a USB capture dongle into OBS
2. **Transcribe** audio with Whisper
3. **Extract on-screen dates** burned into the footage via OCR (helps both tagging and scene splitting)
4. **Tag** videos:
   - Cheap NLP/keyword tagging first, with a confidence score per tag
   - AI fallback tagging (transcript, and possibly key frames) only for videos NLP can't confidently tag
   - Tagging is informed by per-household config of special people and special dates (birthdays, etc.)
5. **Split** long tapes into individual scenes using ffmpeg scene detection, transcript silence gaps, and date changes — transcripts are split and re-timestamped alongside the video rather than regenerated
6. **Upload** finished clips to Jellyfin and apply tags in bulk via Jellytag

## Naming & storage convention

Raw captures and everything derived from them follow one naming scheme so later pipeline stages can always find/match sibling files (transcript, tags, split clips) without a lookup table:

```
raw/{owner}/{tape-id}_{capture-date}.{ext}
```

- `{owner}` — short tag for whose tapes these are (e.g. `julia`, `partner`), matching the per-household config from issue #9
- `{tape-id}` — a stable, sequential ID per physical tape (e.g. `tape001`, `tape042`), zero-padded so files sort in original tape order; label the physical tape itself with this ID for traceability back to the source
- `{capture-date}` — ISO 8601 date (`YYYY-MM-DD`) the *digitization* happened, not the date recorded in the footage (that's extracted separately via OCR, issue #7)

Everything downstream reuses the same base name so files stay associated by naming alone:

```
raw/julia/tape042_2026-07-09.mkv
transcripts/julia/tape042_2026-07-09.json
processed/julia/tape042/scene01.mkv
processed/julia/tape042/scene01.json
```

Split clips (issue #11) get a `sceneNN` suffix under a folder named for the source tape, so a scene's clip and its re-timestamped transcript slice always share a basename.

## Transcript schema

This is the *target* schema for later stages — a source pointer for traceability, a slot for the OCR-extracted date, and per-segment IDs/tags so downstream stages can reference a segment without relying on array position. **`scripts/transcribe.py` does not produce this today**: it currently returns only `language`, `duration`, and `text` (see `tape002_2026-07-15.json`/`tape003_2026-07-15.json` for real output). `source`, `recorded_date`, `segments`, and `tags` get added by later stages (or a future transcribe.py update) that don't exist yet:

```json
{
  "source": "raw/julia/tape001_2026-07-13.mkv",
  "language": "en",
  "duration": 29.6746875,
  "recorded_date": null,
  "text": "Here we are. It's Christmas Eve. Pete, Cat, Annie over...",
  "segments": [
    {
      "id": "s001",
      "start": 0.0,
      "end": 2.96,
      "text": "Here we are. It's Christmas Eve.",
      "tags": []
    }
  ]
}
```

- `source` — path to the raw video this transcript was generated from
- `recorded_date` — ISO 8601 date OCR'd from the footage's on-screen date overlay (issue #7); `null` until that stage runs
- `text` — the full transcript as one string, straight from Whisper; always present, regardless of whether `segments` is available
- `segments` — per-utterance breakdown with timestamps; absent when the Whisper endpoint in use doesn't return segment-level timestamps (our current homelab endpoint only returns whole-clip `text`/`language`/`duration` — see issue #5). Stages needing timestamps (scene splitting, segment-level tagging) must handle a missing `segments` array until a segment-capable endpoint is wired up.
- `segments[].id` — stable ID (`sNNN`, zero-padded, sequential), not the array index — split scenes and tag data reference segments by this ID
- `segments[].tags` — populated by the tagging stage (issue #9's NLP pass, then AI fallback); empty until tagging runs

`tests/fixtures/transcripts/julia/tape001_2026-07-13.json` shows the target shape (hand-edited to add `source`/`recorded_date`/`tags` — `transcribe.py` didn't generate those fields). `tape002_2026-07-15.json` and `tape003_2026-07-15.json` are unmodified `transcribe.py` output and only have `language`/`duration`/`text`.

## Status

Transcribe stage is implemented (`scripts/transcribe.py`, calling a Whisper server on the homelab over SMB) and has a test harness (LLM-as-judge scoring against hand-written goldens, see `issues/plans/002-transcript-testing.md`). Everything else in the pipeline is still planning-stage — see the GitHub issues for task breakdown, dependencies, and open design questions.

Whisper is set up and working on the homelab server. Requires a `.env` (see `.env.example`) with `WHISPER_HOST`, `SAMBA_HOST`, `SAMBA_USERNAME`, `SAMBA_PASSWORD` set, then run via:
```
.venv-whisper/bin/python scripts/transcribe.py <video_path>
```

## Development (planned)

- Dockerized dev environment for parity between a local machine and the server PC
- Local AI stack (Whisper + a local LLM) so development and tests don't depend on cloud services
- Golden-scenario test fixtures covering transcript accuracy, tagging accuracy, scene splitting, and full end-to-end integration
