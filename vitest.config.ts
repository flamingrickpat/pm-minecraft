import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    pool: "threads",
    poolOptions: {
      threads: {
        singleThread: true
      }
    },
    exclude: [
      "tests/e2e/**",
      "node_modules/**",
      "dist/**"
    ]
  }
});
