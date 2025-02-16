/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Nunito', 'sans-serif'],
        display: ['Barriecito', 'cursive'],
        broken: ['"Rubik Broken Fax"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

