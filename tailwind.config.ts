import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#000000",
        panel: "#1C1C1E",
        surface: "#2C2C2E",
        border: "#38383A",
        hover: "#48484A",
        interactive: "#0A84FF",
        "text-primary": "#F5F5F7",
        "text-secondary": "#A1A1A6",
        "text-tertiary": "#6E6E73",
        "track-visual": "#9B8AFF",
        "track-audio": "#5AC8C8",
        "track-technical": "#4ADE80",
        "track-face": "#F5A623",
        "track-metadata": "#FF6B6B",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;
