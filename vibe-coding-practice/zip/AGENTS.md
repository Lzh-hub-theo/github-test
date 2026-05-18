# AGENTS.md

> Replace placeholder text and keep this file compact, command-first, and operational.

## Project Overview

- **Project**: Image Compressor
- **Primary runtime(s)**: Python 3.8+, Flask, Pillow
- **Main entrypoint(s)**: `python server.py` (starts server on port 5000)

## Harness Commands

Run from repository root:

| Goal | Command |
|---|---|
| Fast sanity check | `python server.py` (manual test) |
| Install dependencies | `pip install -r requirements.txt` |
| Full test suite | Manual browser testing |

## Constraints And Guardrails

- Prefer deterministic scripts over interactive/manual steps.
- Keep command names stable (`smoke`, `check`, `test`, `ci`).
- Update docs and scripts in the same change when workflow behavior changes.
- Avoid side effects outside the repo unless explicitly required.

## Architecture Boundaries

- **Frontend**: Single-page app in `public/index.html` - vanilla HTML/CSS/JS, no framework
- **Backend**: Flask API in `server.py` - handles image compression via Pillow
- **API Contract**: POST `/api/compress` (single image), POST `/api/compress-batch` (ZIP), GET `/api/health`

## Observability Expectations

- Include `trace_id` and `run_id` in request/response headers (`X-Trace-ID`, `X-Run-ID`)
- Emit structured JSON events for: `compress_start`, `compress_success`, `compress_error`, `batch_compress_start`, `batch_compress_success`
- Log format: `{"event": "...", "timestamp": "ISO8601", "trace_id": "...", ...}`

## Execution Plans

- For tasks expected to exceed ~30 minutes, create/update `PLANS.md` before coding.
- Track scope, constraints, milestones, and verification steps.
- Update status checkpoints during execution and after major decisions.

## Static Analysis And Quality Gates

- Python syntax check: `python -m py_compile server.py`
- No lint/type tools required for this vanilla Python + HTML project

## Entropy Management

- Remove stale scripts/docs quickly.
- Keep templates and real workflows in sync.
- Run periodic harness audits: `bash scripts/audit_harness.sh .`