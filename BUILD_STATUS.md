# BUILD_STATUS.md

One line per phase. Updated as work progresses so an interrupted session can resume cleanly.

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Repo scaffold (git init, `.gitignore`, LICENSE, directory layout) | done |
| 2 | Python core library (`tracker.py`, `smoothing.py`, `gestures.py`, `pyproject.toml`) | done |
| 2b | Python venv + deps installed, 20 unit tests + smoke tests pass, real-hand test OK | done |
| 3 | Web demo (Vite + TypeScript, `tracker.ts`, `render.ts`, `main.ts`) | in progress |
| 3b | `npm install`, typecheck/build verified | pending |
| 4 | Examples (Air Draw, Volume Control, Virtual Piano, Presentation Remote) | pending |
| 5 | Documentation (root/python/web READMEs, `docs/LANDMARKS.md`, `CONTRIBUTING.md`) | pending |
| 6 | Branding assets (`assets/banner.png`, `assets/logo.png`) | pending |
| — | GitHub: repo topics added, remote set; final push + release pending | pending |
| — | Final test pass, BUILD_STATUS updated, git commit | pending |
