import { defineConfig } from "vite";

// `host: true` exposes the dev server on your LAN so you can open the demo
// from a phone or tablet (great for testing the "works on any device" story).
// Note: browsers only allow camera access from secure contexts — on a phone,
// reach the dev server over HTTPS (e.g. `vite --host` + a tunnel) or serve
// the built files over HTTPS.
export default defineConfig({
  server: {
    host: true,
    port: 5173,
  },
  build: {
    outDir: "dist",
  },
});
