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
| — | PyPI publish workflow (trusted publishing, OIDC) wired + dry-run passed | done |
| — | Web demo: handedness fix + 30fps detection throttle for smoothness | done |
| — | VitePress docs site deployed to Pages (`/docs/`), landmarks case fix | done |
| — | v0.1.2 released: `requires-python <3.13` bound, `__version__` sync; verified end-to-end `pip install openhandtrack` from real PyPI (fresh venv → import → model download → smoke test) | done |
| — | Air Draw: dwell-based colour palette (7 colours) + eraser swatch, keyboard fallback (1-7/e) | done |
| — | One-line TUI installers (`tui.sh` macOS/Linux, `tui.ps1` Windows): detect Python 3.11-3.12, clone, venv, install, interactive example launcher; bash version verified end-to-end in sandbox | done |
| — | Six new examples: finger_count, peace_selfie, virtual_mouse, air_scroll, pinch_ruler, two_hand_zoom (9 total); wired into README/docs/TUI menus | done |
