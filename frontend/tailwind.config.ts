import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#F7F5F0',
        card: '#FFFFFF',
        'subtle-fill': '#EFECE5',
        border: '#DDD8CC',
        'border-subtle': '#DDD8CC',

        'text-primary': '#1A1F2B',
        'text-secondary': '#4A5365',
        'text-muted': '#7A8294',

        'primary-navy': '#1F3A5F',
        'primary-navy-dark': '#142740',
        'accent-saffron': '#C2570C',
        'accent-saffron-light': '#FEF3EB',

        status: {
          green: '#2F7D4F',
          'green-bg': '#EBF7EE',
          amber: '#B7791F',
          'amber-bg': '#FEF7EC',
          red: '#B42318',
          'red-bg': '#FEECEB',
          blue: '#2B5FAE',
          'blue-bg': '#EDF4FC',
        },

        ring: {
          india: '#C2570C',
          'india-bg': '#FEF3EB',
          adversary: '#9B2C2C',
          'adversary-bg': '#FDF2F2',
          regional: '#5B4B8A',
          'regional-bg': '#F4F2F9',
          global: '#2B5FAE',
          'global-bg': '#EDF4FC',
        },
      },
      fontFamily: {
        serif: ['var(--font-source-serif-4)', 'Georgia', 'serif'],
        sans: ['var(--font-ibm-plex-sans)', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;

