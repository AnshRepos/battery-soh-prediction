/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'Consolas', 'monospace'],
        display: ['"Space Grotesk"', 'sans-serif'],
        sans: ['"DM Sans"', 'sans-serif'],
      },
      colors: {
        surface: {
          DEFAULT: '#0a0d14',
          1: '#0f1420',
          2: '#141928',
          3: '#1b2236',
          4: '#232b42',
          border: '#2a3350',
        },
        accent: {
          cyan: '#00e5ff',
          green: '#00ff88',
          amber: '#ffb300',
          rose: '#ff4b6e',
          purple: '#9d7dff',
        },
        text: {
          primary: '#e8edf8',
          secondary: '#8a9abf',
          muted: '#4a5577',
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease forwards',
        'slide-up': 'slideUp 0.4s ease forwards',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
