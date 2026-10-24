/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        graphite: {
          950: '#060911',
          900: '#0a0f1d',
          800: '#111827',
          700: '#1e293b',
          600: '#334155',
          500: '#475569',
        },
        brand: {
          blue: '#3b82f6',
          indigo: '#6366f1',
          purple: '#8b5cf6',
          emerald: '#10b981',
          amber: '#f59e0b',
        }
      }
    },
  },
  plugins: [],
}
