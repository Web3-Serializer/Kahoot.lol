/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {
    colors: { bg:"#09090b", card:"#111113", border:"#1c1c20", muted:"#71717a", accent:"#8b5cf6" },
    fontFamily: { sans:['"DM Sans"','system-ui','sans-serif'], mono:['"JetBrains Mono"','monospace'] },
  }},
  plugins: [],
}
