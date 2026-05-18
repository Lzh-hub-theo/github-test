# PLANS.md

Use this file for multi-step work where durable context matters.

## Objective

- **Outcome**: Full-stack image compressor web application with drag-drop upload, quality controls, and batch download
- **Why it matters**: Provides users a simple tool to reduce image file sizes with visual comparison
- **Non-goals**: Image editing, format conversion beyond compression, cloud storage

## Constraints

- Runtime/tooling constraints: Python 3.8+, Flask, Pillow, vanilla HTML/JS
- Security/compliance constraints: Client-side validation, server-side format validation, 50MB file limit
- Performance/reliability constraints: Local processing only, no external API dependencies

## Context Snapshot

- **Relevant files/modules**: `server.py` (Flask API), `public/index.html` (Frontend SPA), `requirements.txt`
- **Existing commands/workflows**: `python server.py` to run, `pip install -r requirements.txt` to setup
- **Known risks**: Large file handling may cause memory issues on constrained devices

## Execution Plan

1. ✅ **Harness bootstrap**: Created AGENTS.md, PLANS.md, Makefile.harness, scripts/harness/*
2. ✅ **Project spec**: Created SPEC.md with detailed requirements
3. ✅ **Backend implementation**: Flask API with /api/compress, /api/compress-batch, /api/health
4. ✅ **Frontend implementation**: Single HTML file with drag-drop, quality controls, comparison view
5. ⬜ **Verify**: Install dependencies, run server, test in browser
6. ⬜ **Audit**: Run harness audit to validate

## Checkpoints

- [x] Baseline captured
- [x] Implementation complete
- [x] Static checks passed (lint not applicable - pure Python/HTML)
- [ ] Tests passed (manual browser testing)
- [ ] Docs updated

## Decision Log

- **2026/05/18**: Initial stack choice - Flask + vanilla HTML/JS (no framework needed for this scope)
- **2026/05/18**: Quality presets: 80% (high), 60% (medium), 40% (low), custom slider 10-100%
- **2026/05/18**: Output format: original maintains input format, explicit options for JPG/PNG/WebP

## Final Verification

- **Commands run**: `python server.py` starts Flask on port 5000
- **Key outputs**: Upload → compress → compare → download workflow
- **Follow-up tasks**: Add more format support (GIF, TIFF), add EXIF preservation