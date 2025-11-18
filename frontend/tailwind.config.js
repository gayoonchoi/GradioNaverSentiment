/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#5463FF',
        secondary: '#FF1818',
        positive: '#4CAF50',
        negative: '#FF5733',
      }
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
