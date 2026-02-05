/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Antigravity color palette
                cream: {
                    DEFAULT: '#F5F0EB',
                    50: '#FAF8F5',
                    100: '#F5F0EB',
                    200: '#E8DFD6',
                },
                warmstone: {
                    50: '#F9F6F3',
                    100: '#F0EBE5',
                    200: '#E5DDD4',
                    300: '#D4C9BC',
                    400: '#B8A898',
                    500: '#9A8777',
                    600: '#7D6B5C',
                    700: '#5E5045',
                    800: '#403630',
                    900: '#2A2420',
                },
                coral: '#FFE4D6',
            },
            boxShadow: {
                'card': '0 2px 8px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)',
                'card-hover': '0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.06)',
            },
        },
    },
    plugins: [],
}
