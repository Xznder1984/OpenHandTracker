import { defineConfig } from "vitepress";

export default defineConfig({
  title: "OpenHandTrack",
  description: "Real-time 3D hand tracking for Python & the web",
  base: "/OpenHandTracker/",

  head: [
    ["link", { rel: "icon", type: "image/png", href: "/OpenHandTracker/logo.png" }],
  ],

  themeConfig: {
    logo: "/logo.png",
    nav: [
      { text: "Home", link: "/" },
      { text: "Getting Started", link: "/getting-started" },
      { text: "API Reference", link: "/api-reference" },
      { text: "Web Demo", link: "https://xznder1984.github.io/OpenHandTracker/" },
    ],

    sidebar: [
      {
        text: "Guide",
        items: [
          { text: "Introduction", link: "/" },
          { text: "Getting Started", link: "/getting-started" },
          { text: "API Reference", link: "/api-reference" },
          { text: "Landmarks", link: "/landmarks" },
          { text: "Examples", link: "/examples" },
        ],
      },
      {
        text: "Resources",
        items: [
          { text: "Contributing", link: "/contributing" },
          { text: "License", link: "/license" },
        ],
      },
    ],

    socialLinks: [
      { icon: "github", link: "https://github.com/Xznder1984/OpenHandTracker" },
    ],

    search: {
      provider: "local",
    },

    footer: {
      message: "Released under the Apache-2.0 License.",
      copyright: "© 2026 OpenHandTrack Contributors",
    },
  },
});
