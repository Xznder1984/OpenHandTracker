# OpenHandTrack — Web

Real-time hand tracking in the browser: Vite + TypeScript + `@mediapipe/tasks-vision`, rendered on a plain `<canvas>`. No framework, no build complexity — it's meant to be readable as reference code for how to wire MediaPipe's Hand Landmarker into a web project.

## Quickstart

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`, allow camera access, hold your hand up.

That's it. The model (`hand_landmarker.task`, ~7 MB) is fetched from Google's CDN on first load and the wasm runtime is loaded from jsDelivr.

**Try the hosted build**: https://xznder1984.github.io/OpenHandTracker/ — deployed automatically by GitHub Actions on every push to `main`.

## What's in here

| File | What it does |
|------|--------------|
| `src/tracker.ts` | `HandTracker` wrapper around `HandLandmarker` — mirrors the Python API's shape (`HandTracker`, `HandResult`, `Hand`, `Landmark`) so reading both sides feels the same. |
| `src/smoothing.ts` | One-Euro landmark smoothing (TypeScript port of the Python side) — kills frame-to-frame jitter. |
| `src/render.ts` | Canvas skeleton drawing: real bone connections, color-coded left (cyan) vs right (orange). |
| `src/main.ts` | Demo wiring: `getUserMedia`, `requestAnimationFrame` loop, status/FPS overlay. |

`examples/` contains small projects built on top (e.g. a virtual piano).

## API in ~20 lines

```ts
import { HandTracker } from "./tracker";

const tracker = new HandTracker({ maxHands: 2 });   // smoothing on by default
await tracker.initialize();                          // loads the .task model

// in your animation loop:
const result = tracker.detectForVideo(videoElement); // HTMLVideoElement
for (const hand of result.hands) {
  const tip = hand.landmarks[8];                     // index fingertip
  console.log(hand.handedness, hand.confidence, tip.x, tip.y);
}
```

## Running on a phone / tablet

The demo works on any device with a browser and a camera. Two notes:

1. **Secure context**: browsers only expose `getUserMedia` on `https://` (or `localhost`). To test from your phone on the same network, serve over HTTPS — e.g. `npm run dev` for local dev, or `npm run build && npm run preview` and tunnel it.
2. `facingMode: "user"` prefers the front camera, and the layout is responsive.

## The mirrored-handiness quirk (the one that trips everyone up)

An `<video>` element playing a `getUserMedia` feed delivers **unmirrored** pixels. MediaPipe assumes *mirrored* (selfie-style) input when it labels handedness, so the wrapper swaps `Left`/`Right` by default (`mirrored: false`). If you feed it a mirrored source instead, pass `mirrored: true`. Hold up your right hand — if the demo says "Left", flip that flag.

## Build for production

```bash
npm run build     # typechecks + bundles to dist/
npm run preview   # serve the built files locally
```
