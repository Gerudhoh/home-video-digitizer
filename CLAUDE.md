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

## Transcript schema

Transcript JSON extends raw Whisper output with a `source` path, a `recorded_date` slot (filled in by the OCR stage, issue #7), and per-segment `id`/`tags` fields so later stages (scene split, tagging) can reference a segment without relying on array position. Full schema and example in the README's "Transcript schema" section; reference fixture at `tests/fixtures/transcripts/julia/tape001_2026-07-13.json`.

## Where to find current scope

The GitHub issues are the source of truth for task breakdown, open design questions, and dependencies between stages — check them before assuming a design choice not documented here.

As code is added, replace the sections above with real build/lint/test commands and update the architecture description to match what's actually implemented.

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (60-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk go test             # Go test failures only (90%)
rtk jest                # Jest failures only (99.5%)
rtk vitest              # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk pytest              # Python test failures only (90%)
rtk rake test           # Ruby test failures only (90%)
rtk rspec               # RSpec test failures only (60%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%). Format flags (-c, -l, -L, -o, -Z) run raw.
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->