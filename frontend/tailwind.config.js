/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        linkedin: {
          DEFAULT: '#0a66c2',
          dark: '#084298',
          light: '#e7f3ff'
        }
      }
    },
  },
  plugins: [],
}