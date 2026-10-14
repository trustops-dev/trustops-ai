import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  root: fileURLToPath(new URL(".", import.meta.url)),
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["tests/unit/dashboard/**/*.test.{ts,tsx}"],
    setupFiles: ["tests/unit/dashboard/setup.ts"],
    clearMocks: true,
  },
});
