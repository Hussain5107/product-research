import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: "#eef3ff",
          100: "#d9e4ff",
          200: "#b9ccff",
          300: "#8fb2ff",
          400: "#5d8dff",
          500: "#3366ff",
          600: "#2a4be0",
          700: "#223dbb",
          800: "#1d339e",
          900: "#192c84",
          950: "#0f1740",
        },
        electric: {
          400: "#22d3ee",
          500: "#06b6d4",
          600: "#0891b2",
        },
        emerald: {
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
        },
        amber: {
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
        },
        risk: {
          400: "#f87171",
          500: "#ef4444",
          600: "#dc2626",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        xl: "0.75rem",
        "2xl": "0.875rem",
        full: "9999px",
      },
      boxShadow: {
        soft: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        card: "0 4px 12px -2px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.04)",
        elevation: "0 10px 30px -5px rgb(0 0 0 / 0.12), 0 4px 8px -4px rgb(0 0 0 / 0.06)",
      },
    },
  },
  plugins: [],
} satisfies Config;
