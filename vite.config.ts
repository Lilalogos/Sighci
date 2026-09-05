import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // Project Pages live at https://<user>.github.io/SIGHCI_5september/
  base: process.env.GITHUB_ACTIONS ? "/SIGHCI_5september/" : "/",
  plugins: [react()],
  server: { port: 5173, strictPort: true, host: "127.0.0.1" },
});
