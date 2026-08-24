import { defineConfig } from "vite";

// `host: true` exposes the dev server on your LAN so you can open the demo
// from a phone or tablet (great for testing the "works on any device" story).
// Note: browsers only allow camera access from secure contexts — on a phone,
// reach the dev server over HTTPS (e.g. `vite --host` + a tunnel) or serve
// the built files over HTTPS.
export default defineConfig({
  // Visible in the demo status pill so users can confirm which build they run.
  define: { __BUILD_ID__: JSON.stringify("6a8bb2b4") },
  // Relative base so the built demo works when hosted under a subpath
  // (e.g. GitHub Pages at https://xznder1984.github.io/OpenHandTracker/).
  base: "./",
  server: {
    host: true,
    port: 5173,
  },
  build: {
    outDir: "dist",
  },
});
