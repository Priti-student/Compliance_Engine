/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        gov: {
          dark: "#0f2557",
          blue: "#1F3864",
          accent: "#d97706",
          ok: "#1a7f37",
          bad: "#d73a49",
          warn: "#9a6700",
        },
      },
    },
  },
  plugins: [],
};