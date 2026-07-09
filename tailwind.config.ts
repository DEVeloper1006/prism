import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#141416",
        panel: "#1C1C1F",
        surface: "#232326",
        accent: "#6C5CE7",
        good: "#2ED47A",
        warning: "#FFB347",
        bad: "#FF6B6B",
        info: "#4ECDC4",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;
