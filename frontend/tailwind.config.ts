import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: "#0D69A2", // 한국환경공단 Main Blue
                    50: "#E6F3FB",
                    100: "#CCE4F6",
                    200: "#99C9ED",
                    300: "#66ADE3",
                    400: "#3392DA",
                    500: "#0D69A2",
                    600: "#0A5482",
                    700: "#084062", // Deep check
                    800: "#052B41",
                    900: "#031521",
                },
                eco: {
                    DEFAULT: "#96D130", // Eco Green
                    50: "#F4FAE3",
                    100: "#EAF6C8",
                    200: "#D5EC91",
                    300: "#C0E25B",
                    500: "#96D130",
                    600: "#78A726",
                    700: "#5A7D1D",
                },
                sky: {
                    DEFAULT: "#8DD1E0", // Sky Blue
                    50: "#F2FAFC",
                    100: "#E5F6FA",
                    200: "#CCEDF6",
                    500: "#8DD1E0",
                    600: "#71A7B3",
                },
                neutral: {
                    50: "#F8F9FA",
                    100: "#F1F3F5",
                    200: "#E9ECEF",
                    300: "#DEE2E6",
                    400: "#CED4DA",
                    500: "#ADB5BD",
                    600: "#868E96",
                    700: "#495057",
                    800: "#343A40",
                    900: "#212529",
                },
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
                card: "12px",
                pill: "9999px",
            },
            boxShadow: {
                'soft': '0 2px 8px rgba(0, 0, 0, 0.05)',
                'medium': '0 4px 12px rgba(0, 0, 0, 0.08)',
            },
            fontFamily: {
                sans: ['var(--font-pretendard)', 'ui-sans-serif', 'system-ui'],
            }
        },
    },
    plugins: [],
};
export default config;
