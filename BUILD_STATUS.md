# BUILD_STATUS.md

One line per phase. Updated as work progresses so an interrupted session can resume cleanly.

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Repo scaffold (git init, `.gitignore`, LICENSE, directory layout) | done |
| 2 | Python core library (`tracker.py`, `smoothing.py`, `gestures.py`, `pyproject.toml`) | done |
| 2b | Python venv + deps installed, 20 unit tests + smoke tests pass, real-hand test OK | done |
| 3 | Web demo (Vite + TypeScript, `tracker.ts`, `render.ts`, `main.ts`) | done |
| 3b | `npm install`, typecheck/build verified, dev server serves | done |
| 4 | Examples (Air Draw, Volume Control, Virtual Piano, Presentation Remote) | done |
| 5 | Documentation (root/python/web READMEs, `docs/LANDMARKS.md`, `CONTRIBUTING.md`) | done |
| 6 | Branding assets (`assets/banner.png`, `assets/logo.png` via `tools/make_assets.py`) | done |
| — | GitHub: topics added, remote set, description set | done |
| — | Final test pass + commit | done |
| — | Push to GitHub + tag + release (v0.1.0) | done |
| — | CI workflows (ruff+pytest, web typecheck+build) green on `main` | done |
| — | Live demo on GitHub Pages (https://xznder1984.github.io/OpenHandTracker/) | done |
