# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

No pipeline code exists yet — this repo is in the planning stage. The architecture below is the *planned* design, pulled from GitHub issues, not yet implemented. There are no build/lint/test commands to run yet; add them here once code exists.

## Purpose

Scripts to digitize, organize, tag, split, and share home videos: turn raw camcorder/VHS captures into a searchable, tagged library hosted on Jellyfin.

## Planned architecture

The pipeline is a sequence of stages, each consuming/producing files alongside the source video (transcript JSON, tag data, split clips) rather than one monolithic script:

1. **Capture/digitize** — analog tape → digital file, via a USB capture dongle into OBS
2. **Transcribe** (Whisper) — produces a timestamped transcript JSON
3. **Extract dates** — OCR on the burned-in date overlay common to old camcorder footage; feeds both tagging and scene-split decisions
4. **Tag** — two-tier, to minimize AI cost: cheap NLP/keyword tagging with a confidence score runs first; AI (transcript, and possibly sampled key frames) only handles videos NLP can't confidently tag
5. **Scene split** — ffmpeg scene detection + transcript silence gaps + date changes decide split points; transcripts are split and re-timestamped alongside the video, not regenerated
6. **Upload & tag in Jellyfin** — files land in a Jellyfin library via watched-folder + scan (Jellyfin has no true upload API), then tags are applied in bulk via Jellytag

Cross-cutting concerns that span multiple stages:
- **Shared config**: special people/dates (different per household — two people's tapes are being digitized) and tagging confidence thresholds are meant to live in one shared config file read by every tagging stage, not duplicated per stage
- **Idempotency**: each stage should skip videos it has already processed unless explicitly forced, since tapes will be reprocessed as tagging/splitting logic evolves
- **No orchestrator yet**: stages are being built independently; nothing currently wires them into one runnable end-to-end pipeline

## Naming & storage convention

Raw captures and everything derived from them share one naming scheme so pipeline stages can find/match sibling files (transcript, tags, split clips) by name alone, with no lookup table:

```
raw/{owner}/{tape-id}_{capture-date}.{ext}
```

- `{owner}` — short tag for whose tapes these are (e.g. `julia`, `partner`), matching the per-household config from issue #9
- `{tape-id}` — stable, sequential, zero-padded ID per physical tape (e.g. `tape001`), so files sort in original tape order; label the physical tape with this ID too
- `{capture-date}` — ISO 8601 date the *digitization* happened, not the date recorded in the footage (that's extracted separately via OCR, issue #7)

Downstream files reuse the same base name:

```
raw/julia/tape042_2026-07-09.mkv
transcripts/julia/tape042_2026-07-09.json
processed/julia/tape042/scene01.mkv
processed/julia/tape042/scene01.json
```

Split clips (issue #11) get a `sceneNN` suffix under a folder named for the source tape, so a clip and its re-timestamped transcript slice always share a basename.

## Where to find current scope

The GitHub issues are the source of truth for task breakdown, open design questions, and dependencies between stages — check them before assuming a design choice not documented here.

As code is added, replace the sections above with real build/lint/test commands and update the architecture description to match what's actually implemented.
