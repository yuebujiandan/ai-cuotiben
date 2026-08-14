/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: {
          bg: '#FAF7F2',
          card: '#FFFDF8',
          fill: '#F4F0E8'
        },
        inkblue: {
          DEFAULT: '#2B3A67',
          hover: '#22305A',
          deep: '#1C2745'
        },
        error: {
          DEFAULT: '#C0392B',
          bg: '#FCEAE7'
        },
        warn: {
          DEFAULT: '#D9822B',
          bg: '#FBF3E8'
        },
        success: {
          DEFAULT: '#3A7D5C',
          bg: '#EDF4F0'
        },
        infobg: '#EAEFF7'
      },
      borderRadius: {
        tag: '4px',
        btn: '6px',
        card: '10px',
        modal: '12px',
        pill: '20px'
      },
      boxShadow: {
        paper: '0 2px 0 rgba(43,58,103,.06)'
      }
    }
  },
  plugins: []
}
