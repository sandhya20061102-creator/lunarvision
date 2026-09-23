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
          cyan: '#00d4f8',
          blue: '#0088ff',
        }
      },
      animation: {
        'spin-slow': 'spin 40s linear infinite',
        'pulse-slow': 'pulse 4s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
