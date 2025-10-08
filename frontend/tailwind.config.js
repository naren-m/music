/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cultural Carnatic music colors
        saffron: {
          50: '#fff8e1',
          100: '#ffecb3',
          200: '#ffe082',
          300: '#ffd54f',
          400: '#ffca28',
          500: '#ffc107',
          600: '#ffb300',
          700: '#ffa000',
          800: '#ff8f00',
          900: '#ff6f00',
        },
        deepOrange: {
          50: '#fbe9e7',
          100: '#ffccbc',
          200: '#ffab91',
          300: '#ff8a65',
          400: '#ff7043',
          500: '#ff5722',
          600: '#f4511e',
          700: '#e64a19',
          800: '#d84315',
          900: '#bf360c',
        },
        maroon: {
          50: '#fdf2f8',
          100: '#fce7f3',
          200: '#fbcfe8',
          300: '#f9a8d4',
          400: '#f472b6',
          500: '#ec4899',
          600: '#db2777',
          700: '#be185d',
          800: '#9d174d',
          900: '#831843',
        },
        gold: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        earthBrown: {
          50: '#fdf8f6',
          100: '#f2e8e5',
          200: '#eaddd7',
          300: '#e0cfc7',
          400: '#d2bab0',
          500: '#bfa094',
          600: '#a18072',
          700: '#977669',
          800: '#846358',
          900: '#43302b',
        }
      },
      fontFamily: {
        'devanagari': ['Noto Sans Devanagari', 'serif'],
        'english': ['Inter', 'system-ui', 'sans-serif'],
        'carnatic': ['Noto Sans Tamil', 'serif'],
      },
      animation: {
        'wave': 'wave 2s linear infinite',
        'pitch-pulse': 'pitchPulse 1s ease-in-out infinite alternate',
        'raga-flow': 'ragaFlow 3s ease-in-out infinite',
        'swara-glow': 'swaraGlow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        wave: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' }
        },
        pitchPulse: {
          '0%': { transform: 'scale(1)', opacity: '0.8' },
          '100%': { transform: 'scale(1.05)', opacity: '1' }
        },
        ragaFlow: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' }
        },
        swaraGlow: {
          '0%': { boxShadow: '0 0 5px rgba(255, 193, 7, 0.5)' },
          '100%': { boxShadow: '0 0 20px rgba(255, 193, 7, 0.8)' }
        }
      },
      backdropBlur: {
        xs: '2px',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}