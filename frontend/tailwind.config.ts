import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        drape: {
          obsidian: '#0A0A0B',
          charcoal: '#1C1C1E',
          'charcoal-light': '#2C2C2E',
          bone: '#F5F0E8',
          cream: '#FAFAF7',
          gold: '#C9A96E',
          'gold-light': '#E8D5A3',
          'gold-dark': '#A67C52',
          mist: '#8E8E93',
          'mist-dark': '#636366',
          ivory: '#FFFFF0',
        },
      },
      fontFamily: {
        display: ['Playfair Display', 'Georgia', 'serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      animation: {
        shimmer: 'shimmer 2s linear infinite',
        fadeUp: 'fadeUp 0.5s ease-out',
        scaleIn: 'scaleIn 0.3s ease-out',
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      backgroundImage: {
        'shimmer-gradient': 'linear-gradient(90deg, transparent 0%, rgba(201,169,110,0.1) 50%, transparent 100%)',
      },
    },
  },
  plugins: [],
} satisfies Config
