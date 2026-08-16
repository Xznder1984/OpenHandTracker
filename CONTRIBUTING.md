# Contributing to OpenHandTrack

Thanks for helping out! This project is small on purpose — readable code over
clever code, so people can learn how MediaPipe wrapping works from it.

## Setup

```bash
git clone https://github.com/Xznder1984/OpenHandTracker
cd OpenHandTracker

# Python side
python -m venv .venv
.venv/bin/pip install -e "python/[dev,examples]"

# Web side
cd web && npm install
```

## Running tests

Python (no camera, no model download — pure logic):

```bash
.venv/bin/python -m pytest python/
```

Web (typecheck + production build):

```bash
cd web
npm run typecheck
npm run build
```

The full `npm run build` runs the typecheck first. The virtual-piano example
is its own npm package — run its `npm run build` too if you touch `web/`.

## Code style

- **Python**: ruff with the config in `python/pyproject.toml`
  (100 columns, `ruff check .` from `python/`). Type hints everywhere —
  this is a library other people read.
- **TypeScript**: `strict: true` in `web/tsconfig.json`; no `any` unless it's
  a deliberate duck-typing boundary.
- Docstrings/comments: explain *why*, not *what*. Public Python functions get
  docstrings; internal helpers get one line where useful.

## Adding a new example

This is the most common contribution and the one with the most value — the
whole point of the library is "look how little code a hand-tracking app
needs."

1. Create `python/examples/<name>/` or `web/examples/<name>/`.
2. Reuse `HandTracker` (and `gestures.py` / `tracker.ts`) — **never**
   reimplement tracking logic inside an example.
3. Keep it short (~100–150 lines) and genuinely runnable, with graceful
   handling for missing webcam / missing platform tools.
4. Add a small `README.md`: what it does, how to run it, the gesture→action
   table.
5. If it needs a new dependency, add it to the `examples` extra in
   `python/pyproject.toml` (with a `sys_platform` marker if it's
   platform-specific).

## Documentation

- Public API changes → update `python/README.md` / `web/README.md` and the
  API table.
- Landmark index changes (unlikely) → update `docs/LANDMARKS.md`.

## Commits

Keep commits small and scoped (`python: …`, `web: …`, `docs: …`), one logical
change each.

## Releasing (maintainers)

1. Bump `version` in `python/pyproject.toml` (keep it in sync with `openhandtrack/__init__.py`).
2. Tag and publish a GitHub release — `.github/workflows/publish-pypi.yml` builds the sdist + wheel and publishes to PyPI automatically.
3. Confirm on [pypi.org/project/openhandtrack](https://pypi.org/project/openhandtrack/).

**One-time trusted-publisher setup** (no token/secrets to store): on PyPI go to
*Account → Publishing → Add a new pending publisher* and grant **GitHub** with:

- Owner: `Xznder1984`
- Repository: `OpenHandTracker`
- Workflow name: `publish-pypi.yml`

## License

By contributing you agree your changes are licensed under Apache-2.0 (see
`LICENSE`).
