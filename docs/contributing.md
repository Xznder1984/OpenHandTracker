# Contributing

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

# Docs (optional)
cd ../docs && npm install
```

## Running Tests

Python (no camera needed — pure logic):

```bash
.venv/bin/python -m pytest python/
```

Web (typecheck + production build):

```bash
cd web
npm run build
```

Docs (dev server):

```bash
cd docs
npm run dev
```

## Code Style

- **Python**: ruff with the config in `python/pyproject.toml`
  (100 columns). Type hints everywhere.
- **TypeScript**: `strict: true` in `web/tsconfig.json`; no `any` unless it's
  a deliberate duck-typing boundary.

## Adding an Example

1. Create `python/examples/<name>/` or `web/examples/<name>/`.
2. Reuse `HandTracker` and `gestures.py` / `tracker.ts` — never reimplement
   tracking logic inside an example.
3. Keep it short (~100–150 lines) and genuinely runnable.
4. Add a small `README.md`: what it does, how to run it, the gesture→action table.
5. If it needs a new dependency, add it to the `examples` extra in
   `python/pyproject.toml` (with a `sys_platform` marker if platform-specific).

## Documentation

- Public API changes → update `docs/api-reference.md` and `python/README.md`.
- Landmark changes → update `docs/landmarks.md`.

## Commits

Keep commits small and scoped (`python: …`, `web: …`, `docs: …`), one logical
change each.

## License

By contributing you agree your changes are licensed under Apache-2.0.
