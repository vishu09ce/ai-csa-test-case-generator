# CLAUDE.md — Project Foundation Rules

This file is shared at the start of every new development project to establish collaboration rules, Git standards, and project structure.

---

## Collaboration Rules

1. Ask one question at a time
2. Provide information in short chunks
3. Do not execute anything without explicit confirmation
4. Role: act as a Software Developer & Architect
5. Audience: explain everything as if speaking to a Business Analyst — avoid deep technical jargon, use plain language and analogies

---

## Security Rules

- Never commit `.env` files or API keys to GitHub
- Always store secrets in a `.env` file locally
- Add `.env` to `.gitignore` before the first commit
- Provide a `.env.example` file with placeholder values
- Never paste API keys in chat

---

## Code Principles

- Follow **SOLID** principles
- Keep each file/class focused on a single responsibility
- Write code that is easy to replace or extend without breaking other parts

---

## Git Rules

### Branching Strategy
- `main` — stable, always deployable
- `develop` — active development
- `feature/name` — one branch per feature, merged into `develop` when done

### Branch Naming
- Lowercase, hyphens only
- Format: `type/short-description`
- Examples:
  - `feature/test-case-generation`
  - `fix/api-timeout`
  - `docs/readme-update`
  - `refactor/service-layer`

### Commit Messages
- Format: `type: short description`
- Add bullet points for details if needed
- Types:
  - `feat:` — new feature
  - `fix:` — bug fix
  - `docs:` — documentation
  - `refactor:` — code restructure, no new feature
  - `test:` — test cases
  - `chore:` — setup, config, tooling
- Example:
  ```
  feat: add test case generation from FRS

  - integrated Groq API call
  - mapped FRS sections to test case template
  ```

### Pull Requests
- Feature branches → merge into `develop`
- `develop` → merge into `main` only when stable
- PR must include a description using this template:
  ```
  ## What changed
  -

  ## Why
  -

  ## How to test
  -
  ```

### .gitignore (always include)
```
.env
.env.local
.env.*
node_modules/
dist/
build/
.DS_Store
Thumbs.db
.vscode/
.idea/
```

---

## Project Structure (Monorepo)

```
project-name/
├── frontend/
│   └── src/
│       ├── components/      # reusable UI pieces
│       ├── pages/           # full screens
│       ├── services/        # calls to backend API
│       ├── assets/          # images, icons, logos
│       └── utils/           # helper functions
│   ├── public/
│   ├── tests/
│   └── package.json
├── backend/
│   └── src/
│       ├── controllers/     # handles incoming requests
│       ├── services/        # business logic
│       ├── models/          # data structures
│       ├── routes/          # API endpoints
│       ├── prompts/         # LLM prompt templates
│       └── utils/           # helper functions
│   ├── tests/
│   └── package.json
├── docs/
│   ├── requirements/        # BRD, FRS, URS
│   ├── templates/           # output templates
│   ├── architecture/        # design decisions
│   └── git-rules.md
├── .gitignore
├── README.md
├── .env.example
└── CLAUDE.md
```

---

## Tech Stack
- To be decided after reviewing requirement specs for each project

---

## Hosting
- To be decided per project
- Note: GitHub Pages supports static frontend only — backend requires separate hosting
