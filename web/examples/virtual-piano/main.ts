/**
 * Virtual Piano — index fingertip + pinch to play, Web Audio for the sound.
 *
 * Reuses the shared OpenHandTrack web wrapper (../../src/tracker.ts) so the
 * whole example is ~130 lines of gesture + rendering + audio.
 *
 * Interaction: the bottom half of the canvas is the keyboard. When you pinch
 * (thumb+index) with your fingertip over a key, that key sounds. Slide while
 * pinching for a glissando; release the pinch to stop playing.
 */

import { HandTracker } from "../../src/tracker";

// ---------------------------------------------------------------- audio
const audio = new AudioContext();

function noteFreq(midi: number): number {
  return 440 * Math.pow(2, (midi - 69) / 12);
}

function playNote(midi: number): void {
  const osc = audio.createOscillator();
  const gain = audio.createGain();
  osc.type = "triangle";
  osc.frequency.value = noteFreq(midi);
  gain.gain.setValueAtTime(0.0001, audio.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.35, audio.currentTime + 0.015);
  gain.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + 0.9);
  osc.connect(gain).connect(audio.destination);
  osc.start();
  osc.stop(audio.currentTime + 0.95);
}

// ---------------------------------------------------------------- keyboard layout
// Two octaves, C4 (MIDI 60) .. B5 (MIDI 83).
const OCTAVE = [0, 2, 4, 5, 7, 9, 11]; // C D E F G A B offsets
const KEYS: { midi: number; white: boolean; x: number; w: number }[] = [];
const WHITE_WIDTH = 1 / 14; // 14 white keys across two octaves

for (let octave = 4; octave <= 5; octave++) {
  for (const offset of OCTAVE) {
    KEYS.push({ midi: 12 * (octave + 1) + offset, white: true, x: KEYS.filter((k) => k.white).length * WHITE_WIDTH, w: WHITE_WIDTH });
  }
}
// Black keys: semitone-above-prev-natural positions.
for (let octave = 4; octave <= 5; octave++) {
  for (const offset of [1, 3, 6, 8, 10]) {
    const naturalCount = KEYS.filter((k) => k.white && k.midi < 12 * (octave + 1) + offset).length;
    KEYS.push({ midi: 12 * (octave + 1) + offset, white: false, x: naturalCount * WHITE_WIDTH - 0.03, w: 0.06 });
  }
}
KEYS.sort((a, b) => a.x - b.x);

// ---------------------------------------------------------------- dom
const canvas = document.querySelector<HTMLCanvasElement>("#app")!;
const ctx = canvas.getContext("2d")!;
const statusEl = document.querySelector<HTMLDivElement>("#status")!;
const video = document.createElement("video");
video.autoplay = true;
video.muted = true;
video.playsInline = true;

const KEYBOARD_Y = 0.5; // keys occupy the bottom half of the canvas
const currentKey: Map<string, number> = new Map(); // handedness -> playing midi

// ---------------------------------------------------------------- rendering
function drawPiano(): void {
  const { width, height } = ctx.canvas;
  const top = height * KEYBOARD_Y;

  for (const key of KEYS) {
    const x = key.x * width;
    const w = key.w * width;
    if (key.white) {
      ctx.fillStyle = "#f8fafc";
      ctx.fillRect(x, top, w, height - top);
      ctx.strokeStyle = "#94a3b8";
      ctx.strokeRect(x + 0.5, top, w, height - top);
    }
  }
  for (const key of KEYS) {
    if (key.white) continue;
    const x = key.x * width;
    const w = key.w * width;
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(x, top, w, (height - top) * 0.62);
    ctx.strokeStyle = "#334155";
    ctx.strokeRect(x, top, w, (height - top) * 0.62);
  }

  // Highlight the keys currently being played.
  for (const midi of currentKey.values()) {
    const key = KEYS.find((k) => k.midi === midi)!;
    ctx.fillStyle = key.white ? "#22d3ee" : "#0891b2";
    ctx.fillRect(key.x * width, top, key.w * width, height - top);
  }
}

function keyAt(xNorm: number, yNorm: number): { midi: number } | null {
  if (yNorm < KEYBOARD_Y) return null;
  const key = KEYS.find((k) => xNorm >= k.x && xNorm <= k.x + k.w);
  return key ? { midi: key.midi } : null;
}

// ---------------------------------------------------------------- main
async function main(): Promise<void> {
  statusEl.textContent = "Loading model…";
  const tracker = new HandTracker({ maxHands: 2, smoothing: true });
  try {
    await tracker.initialize();
  } catch (err) {
    statusEl.textContent = `Model load failed: ${String(err)}`;
    throw err;
  }

  if (!navigator.mediaDevices?.getUserMedia) {
    statusEl.textContent = "getUserMedia not supported in this browser.";
    return;
  }
  video.srcObject = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "user" },
    audio: false,
  });
  await video.play();

  const loop = () => {
    requestAnimationFrame(loop);

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const result = tracker.detectForVideo(video);
    drawPiano();

    const playingNow = new Set<string>();

    for (const hand of result.hands) {
      const tip = hand.landmarks[8]; // index fingertip
      const pressed = keyAt(tip.x, tip.y);
      const pinching = Math.hypot(
        hand.landmarks[4].x - tip.x,
        hand.landmarks[4].y - tip.y,
      ) < 0.06; // thumb tip near index tip = pinch

      if (pressed && pinching) {
        const prev = currentKey.get(hand.handedness);
        if (prev !== pressed.midi) {
          playNote(pressed.midi);
          currentKey.set(hand.handedness, pressed.midi);
        }
        playingNow.add(hand.handedness);
      }
    }

    for (const [label, midi] of currentKey) {
      if (!playingNow.has(label)) currentKey.delete(label);
    }

    statusEl.textContent = result.hands.length
      ? `${result.hands.length} hand(s) — pinch over a key to play`
      : "No hand in frame";
  };
  loop();
}

main().catch((err) => console.error(err));
