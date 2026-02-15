/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#070b12',
        panel: '#0f1521',
        panelSoft: '#121c2b',
        borderSoft: '#253146'
      }
    }
  },
  plugins: []
};
