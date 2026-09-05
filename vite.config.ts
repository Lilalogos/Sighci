import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const repoName = process.env.GITHUB_REPOSITORY?.split("/")[1];

export default defineConfig({
  // Project Pages: https://<user>.github.io/<repo>/
  base: process.env.GITHUB_ACTIONS && repoName ? `/${repoName}/` : "/",
  plugins: [react()],
  server: { port: 5173, strictPort: true, host: "127.0.0.1" },
});
