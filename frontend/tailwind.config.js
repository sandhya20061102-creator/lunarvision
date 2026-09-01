/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        lunar: {
          950: '#06090f',
          900: '#0b111e',
          800: '#141d2e',
          700: '#1e2c45',
          600: '#2d3f61',
          500: '#465e8a',
          400: '#738db5',
          300: '#a3b8d6',
          200: '#d1dcf0',
          100: '#edf2fa',
        },
        glow: {
          cyan: '#00f2fe',
          blue: '#4facfe',
        }
      },
    },
  },
  plugins: [],
}
