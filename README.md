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

## Status

Early planning stage — no pipeline code yet. See the GitHub issues for the current task breakdown, dependencies between stages, and open design questions.

## Development (planned)

- Dockerized dev environment for parity between a local machine and the server PC
- Local AI stack (Whisper + a local LLM) so development and tests don't depend on cloud services
- Golden-scenario test fixtures covering transcript accuracy, tagging accuracy, scene splitting, and full end-to-end integration
