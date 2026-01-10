import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: 'rgba(148, 163, 184, 0.2)',
        background: '#05070a',
        foreground: '#e5e7eb',
      },
    },
  },
} satisfies Config
