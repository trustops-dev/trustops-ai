import { defineConfig, globalIgnores } from "eslint/config";
import js from "@eslint/js";
import jsxA11y from "eslint-plugin-jsx-a11y";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig([
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.tsx"],
    extends: [
      react.configs.flat.recommended,
      react.configs.flat["jsx-runtime"],
      reactHooks.configs.flat.recommended,
      jsxA11y.flatConfigs.recommended,
    ],
    languageOptions: { globals: globals.browser },
    settings: { react: { version: "detect" } },
    rules: { "react/prop-types": "off" }, // TypeScript validates component props.
  },
  {
    files: ["**/*.{mjs,mts}"],
    languageOptions: { globals: globals.node },
  },
  globalIgnores([
    "**/.next/**",
    "**/out/**",
    "**/build/**",
    "**/next-env.d.ts",
    "**/coverage/**",
    ".venv/**",
  ]),
]);
