import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        border: "var(--border)",
        ring: "var(--ring)",
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        ink: {
          DEFAULT: "#101418",
          soft: "#1C242C",
          muted: "#5A6672",
        },
        paper: {
          DEFAULT: "#F2F4F1",
          warm: "#E8ECE6",
          deep: "#D5DCD4",
        },
        signal: {
          DEFAULT: "#0C8F6A",
          bright: "#12B886",
          dim: "#0A6B50",
        },
        alert: {
          DEFAULT: "#C23B3B",
          soft: "#E8B4B4",
        },
        mist: "#9AA7B2",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        lift: "0 20px 50px -24px rgba(16, 20, 24, 0.35)",
      },
      backgroundImage: {
        mesh: "radial-gradient(ellipse 80% 60% at 10% 20%, rgba(12,143,106,0.18), transparent 55%), radial-gradient(ellipse 70% 50% at 90% 10%, rgba(61,90,128,0.16), transparent 50%), radial-gradient(ellipse 60% 40% at 50% 100%, rgba(16,20,24,0.08), transparent 45%)",
        chart: "linear-gradient(180deg, rgba(12,143,106,0.12) 0%, transparent 70%)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(18px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.55" },
          "50%": { opacity: "1" },
        },
        drift: {
          "0%": { transform: "translate3d(0,0,0)" },
          "50%": { transform: "translate3d(12px,-8px,0)" },
          "100%": { transform: "translate3d(0,0,0)" },
        },
      },
      animation: {
        rise: "rise 0.7s ease-out both",
        "pulse-soft": "pulseSoft 3.2s ease-in-out infinite",
        drift: "drift 14s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
