import type { Config } from "tailwindcss";
import rtl from "tailwindcss-rtl";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        quran: ['"Scheherazade New"', "serif"],
        ui: ['"IBM Plex Arabic"', "sans-serif"],
      },
      fontSize: {
        quran: ["22px", { lineHeight: "2.2" }],
        "quran-lg": ["28px", { lineHeight: "2.4" }],
      },
      colors: {
        primary: {
          50: "#f0f9f4",
          100: "#d9f0e3",
          200: "#b5e1ca",
          300: "#84cba8",
          400: "#50b083",
          500: "#2d9567",
          600: "#1e7852",
          700: "#186043",
          800: "#154d37",
          900: "#12402f",
        },
      },
    },
  },
  plugins: [rtl],
};

export default config;
