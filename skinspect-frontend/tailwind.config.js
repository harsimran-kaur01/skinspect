/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1B1D18",
        paper: "#F2F1EA",
        sage: {
          DEFAULT: "#4F5F4A",
          light: "#6E7E68",
          dark: "#3A4636",
          50: "#EEF1EC",
        },
        clay: {
          DEFAULT: "#A97C68",
          light: "#C29B89",
          50: "#F5EDE9",
        },
        line: "#DFDACE",
        alert: "#A64C41",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        sans: ["Inter", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(27, 29, 24, 0.04)",
      },
      keyframes: {
        scanSweep: {
          "0%": { transform: "translateY(-100%)", opacity: "0" },
          "10%": { opacity: "1" },
          "90%": { opacity: "1" },
          "100%": { transform: "translateY(100%)", opacity: "0" },
        },
      },
      animation: {
        "scan-sweep": "scanSweep 1.4s ease-in-out forwards",
      },
    },
  },
  plugins: [],
}