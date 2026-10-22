// A deliberately small lint: the recommended JavaScript and TypeScript rules,
// plus the two React hook rules that catch real bugs. Formatting is not linted.
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'CultureForge AI', 'graphify-out', '.opencode', '.agents', '.venv'] },
  {
    files: ['src/**/*.{ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: { ecmaVersion: 2020, globals: globals.browser },
    plugins: { 'react-hooks': reactHooks },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
  {
    files: ['main.js'],
    extends: [js.configs.recommended],
    languageOptions: { ecmaVersion: 2022, sourceType: 'module', globals: { ...globals.browser, Motion: 'readonly' } },
  },
  {
    files: ['scripts/**/*.mjs', '*.config.{js,ts}', 'vite.config.ts'],
    extends: [js.configs.recommended],
    languageOptions: { ecmaVersion: 2022, sourceType: 'module', globals: globals.node },
  },
  {
    files: ['vite.config.ts'],
    extends: [...tseslint.configs.recommended],
  },
)
