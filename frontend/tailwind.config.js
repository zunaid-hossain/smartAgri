/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        field: "#256d3b",
        earth: "#7a5c36",
        water: "#1b7aa7",
        warning: "#c47c1d",
      },
      boxShadow: {
        panel: "0 12px 40px rgba(25, 43, 31, 0.08)",
      },
    },
  },
  plugins: [],
};
