import hooks from "eslint-plugin-react-hooks";
import a11y from "eslint-plugin-jsx-a11y";
export default [
  { ignores: ["dist/**", "node_modules/**", "coverage/**"] },
  {
    files: ["src/**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: Object.fromEntries(
        [
          "window",
          "document",
          "navigator",
          "location",
          "fetch",
          "Blob",
          "URL",
          "URLSearchParams",
          "AbortController",
          "BroadcastChannel",
          "setTimeout",
          "clearTimeout",
          "requestAnimationFrame",
          "queueMicrotask",
          "HTMLDialogElement",
          "DOMException",
          "FileReader",
          "FormData",
          "HTMLAnchorElement",
        ].map((name) => [name, "readonly"]),
      ),
    },
    plugins: { "react-hooks": hooks, "jsx-a11y": a11y },
    rules: {
      "no-undef": "error",
      ...hooks.configs.recommended.rules,
      ...a11y.flatConfigs.recommended.rules,
    },
  },
];
