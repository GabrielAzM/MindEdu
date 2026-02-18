import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#102a43",
        mist: "#f2f7ff",
        sky: "#d9ecff",
        mint: "#d6f5e8",
        coral: "#ffcabd",
      },
      borderRadius: {
        lg: "0.75rem",
      },
      fontFamily: {
        heading: ["Trebuchet MS", "sans-serif"],
        body: ["Verdana", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
