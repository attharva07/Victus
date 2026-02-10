import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(220 16% 85%)',
        background: 'hsl(220 33% 98%)',
        foreground: 'hsl(224 26% 12%)',
        card: 'hsl(0 0% 100%)',
        muted: 'hsl(220 14% 96%)',
      },
      boxShadow: {
        card: '0 8px 24px rgba(16, 24, 40, 0.06)',
      },
    },
  },
  plugins: [],
} satisfies Config;
