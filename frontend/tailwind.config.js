/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ls-blue':       '#1565C0',
        'ls-blue-mid':   '#1E88E5',
        'ls-blue-light': '#42A5F5',
        'ls-blue-pale':  '#E3F0FC',
        'ls-green':      '#7CB342',
        'ls-green-light':'#EEF7E0',
      },
    },
  },
  plugins: [],
}
