# Virtual Piano 🎹

Play a piano with your hands — no keyboard, no sample files. Notes are
synthesized live with the Web Audio API.

The bottom half of the screen is a two-octave keyboard (C4–B5). Pinch your
thumb and index together with your fingertip over a key to strike it; slide
while pinching for a glissando; release the pinch to stop.

## Run

```bash
cd web/examples/virtual-piano
npm install
npm run dev
```

Open `http://localhost:5174` and allow camera access. On a phone, serve over
HTTPS (browsers require a secure context for camera access) — see the main
`web/README.md`.

## How it works

- Reuses `../../src/tracker.ts` (the shared `HandTracker` wrapper) — no
  tracking code is rewritten here.
- The index fingertip (landmark 8) is hit-tested against the key layout.
- A thumb-tip-to-index-tip gap under `0.06` (normalized) counts as a pinch.
- Each strike creates an `OscillatorNode` + `GainNode` envelope in Web Audio
  (triangle wave, ~0.9 s decay) — that's the whole synth.
