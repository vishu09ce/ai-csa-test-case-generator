# AI-Powered CSA Validation Document Generator

Built on the principle that **AI accelerates, humans decide** — a production-deployed, full-stack application that generates a complete FDA CSA-compliant validation document package from uploaded source documents, with human review architecturally enforced at every stage. Reduces a multi-day manual process to minutes for Life Sciences organisations.

🔗 [Live Demo](https://vishu09ce.github.io/ai-csa-test-case-generator/) | [Backend API](https://ai-csa-backend.onrender.com)

---

## The Problem

Producing FDA CSA validation documentation is one of the most time-consuming, repetitive, and error-prone activities in Life Sciences software implementation. Validation teams manually translate URS and FRS requirements into test protocols, traceability matrices, and summary reports — a process that takes days and introduces inconsistency at every step.

This application uses AI to generate a complete, structured validation document package in minutes — grounded in the actual source documents uploaded by the user, not generic templates.

---

## Why It Matters

The FDA's 2025 Computer Software Assurance guidance shifts the industry away from documentation-heavy validation toward risk-based, outcome-focused assurance. This tool is purpose-built for that paradigm — AI-accelerated document generation with human review architecturally enforced at every stage.

---

## What It Does

Accepts URS and FRS as required inputs (BRD optional) and generates six sequential, gate-controlled validation documents:

| # | Document | Purpose |
|---|---|---|
| 1 | Software Assurance Plan (SAP) | Defines the validation strategy and risk approach |
| 2 | Process Risk Assessment (PRA) | Identifies and scores process risks |
| 3 | Requirements Traceability Matrix (RTM) | Maps every requirement to a test case |
| 4 | Scripted Test Protocol + Execution Record (STP) | Structured, step-by-step test scripts |
| 5 | Unscripted Test Record + Execution Record (UTR) | Exploratory testing documentation |
| 6 | Assurance Summary Report (ASR) | Final validation summary for regulatory submission |

**Key capabilities:**

- **HITL gate-controlled workflow** — human review enforced before advancing to each next document; AI output is never auto-approved
- **Per-requirement RAG context** — each test case grounded in pinpointed FRS/BRD content, not the full document
- **11-rule output validation with auto-correction** before any document is saved
- **Parallel generation** — up to 5 concurrent LLM calls with exponential backoff on rate limits
- **Resume capability** — interrupted runs skip already-completed requirements on restart
- **Downloadable Word + PDF output** for every document
- **Live progress tracking** — real-time generation banner in the UI
- **164 backend tests** across models, routes, RAG service, validation, and resilience

---

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| HITL design | Gate-controlled, architecturally enforced | Reflects real GxP review requirements; AI output is never auto-approved |
| RAG approach | Per-requirement context retrieval | Prevents context window dilution; improves test case specificity |
| Output validation | 11-rule check + auto-correction | Ensures structural compliance before any document is saved |
| LLM abstraction | LiteLLM | Provider-agnostic layer enables switching LLMs without code changes |
| LLM provider | Groq (llama3-70b) | High-throughput inference suitable for parallel generation workloads |
| Parallelism | 5 concurrent calls + exponential backoff | Balances generation speed against API rate limits |
| Deployment | Docker on Render + GitHub Pages | Production-grade, zero-cost infrastructure for a PoC |
| Database | SQLite + SQLAlchemy | Lightweight persistence with resume capability |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS → GitHub Pages |
| Backend | Python + FastAPI + SQLite → Render (Docker) |
| LLM Abstraction | LiteLLM |
| LLM Provider | Groq (llama3-70b) |
| PDF Generation | LibreOffice via docx2pdf |
| CI/CD | GitHub Actions |

---

## Future Roadmap

- [ ] Expand to support 21 CFR Part 11 audit trail generation
- [ ] Add confidence scoring per generated requirement
- [ ] Multi-user support with role-based HITL assignment
- [ ] Integration with eQMS platforms (Veeva Vault, MasterControl)
- [ ] LLM provider benchmarking for CSA document quality
- [ ] Support for IQ/OQ/PQ protocol generation

---

## Development Approach

This application was built using Claude Code as an AI-assisted development environment. All architectural decisions — including RAG pipeline design, HITL workflow enforcement, output validation logic, parallel generation strategy, and deployment architecture — were directed, validated, and owned by the author.

AI-assisted development is treated here as a professional productivity tool, equivalent to using a framework or IDE.

---

*Built by **Vashishth Purohit** — AI Solutions Consultant | Life Sciences & Healthcare IT*
