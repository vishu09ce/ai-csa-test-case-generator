# Git Rules

## Branching Strategy
- `main` — stable, always deployable
- `develop` — active development
- `feature/name` — one branch per feature, merged into `develop` when done

## Branch Naming
- Lowercase, hyphens only
- Format: `type/short-description`
- Examples:
  - `feature/test-case-generation`
  - `fix/api-timeout`
  - `docs/readme-update`
  - `refactor/service-layer`

## Commit Messages
- Format: `type: short description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- Example:
  ```
  feat: add test case generation from FRS

  - integrated Groq API call
  - mapped FRS sections to test case template
  ```

## Pull Requests
- Feature branches → merge into `develop`
- `develop` → merge into `main` only when stable
- PR description template:
  ```
  ## What changed
  -

  ## Why
  -

  ## How to test
  -
  ```

## .gitignore
- `.env`, `node_modules/`, `dist/`, `.DS_Store`, `.vscode/`
