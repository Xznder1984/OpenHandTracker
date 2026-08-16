import { defineConfig } from "vite";

// This example imports the shared wrapper from ../../src, so Vite must be
// allowed to serve files above this folder's root.
export default defineConfig({
  server: {
    host: true,
    port: 5174,
    fs: { allow: ["../.."] },
  },
});
