import { defineConfig } from 'vite'

export default defineConfig({
  root: '.',         // default, but be explicit
  server: {
    host: true,      // 0.0.0.0 inside container
    port: 5173,
    strictPort: true,
    hmr: {
      host: 'localhost',  // dev convenience
      port: 5173,
    },
  },
})
