# MolGenix - Engineering Decisions

MolGenix is an AI-powered biomedical drug discovery prototype built to demonstrate a complete product workflow: natural-language target identification, molecule ranking, ADMET review, molecular visualization, and downloadable research-style reports.

This document records the major architectural, engineering, product, and design decisions behind the MVP. It is intentionally scoped to the demo implementation and should be read as an engineering decision log, not as scientific validation documentation.

## 1. Project Philosophy

MolGenix is intentionally lightweight. The project is designed to communicate a credible end-to-end drug discovery workflow without the infrastructure, validation burden, or computational cost of a real pharmaceutical platform.

The main priorities are:

- Clear demonstration value for portfolio, hackathon, and review settings.
- Fast local startup with minimal setup.
- A realistic product narrative without claiming real biomedical validity.
- Educational clarity for contributors and reviewers.
- A clean architecture that can be extended after the prototype.

The system favors clarity over scientific complexity. A production-grade discovery platform would require validated datasets, domain-specific modeling, real docking workflows, assay evidence, regulatory review, and expert scientific oversight. MolGenix instead focuses on showing how such a workflow could be structured as a product.

## 2. Why Mock Data Was Used

MolGenix uses mock data by design. Real pharmaceutical datasets introduce licensing concerns, data normalization work, domain-specific validation requirements, and scientific interpretation risks that are outside the scope of the MVP.

The mock-data approach provides:

- Deterministic demos.
- Reproducible test results.
- Fast local performance.
- Offline behavior when external AI APIs are unavailable.
- No dependency on real pharmaceutical databases.
- Lower legal and operational complexity.

The seed dataset is deliberately constrained:

- Exactly 5 predefined drug targets.
- Exactly 40 molecules.
- Exactly 8 molecules per target.
- Simulated docking scores.
- Simulated ADMET values.
- Intentional toxicity flags for demonstration.

This makes the demo predictable while still realistic enough to show target matching, ranking, filtering, visualization, and reporting.

## 3. Backend Architecture Decisions

FastAPI was selected because it fits the needs of a rapid MVP while still supporting clean production-style organization.

Key reasons:

- Strong developer experience.
- Built-in OpenAPI and Swagger UI.
- Simple request validation through Pydantic.
- Good async support for future expansion.
- Low friction for local and Docker deployment.

The backend is organized into separate modules for:

- `models`
- `schemas`
- `services`
- `routers`
- `utils`
- `mock_data`

This separation keeps domain objects, API contracts, business logic, routing, utilities, and seed data independent. The structure is intentionally modest, but it gives the project a scalable foundation for future phases.

SQLAlchemy was chosen for database access because it provides a mature ORM, SQLAlchemy 2.x typing patterns, relationship modeling, and a clear path to PostgreSQL if the prototype evolves. Pydantic was selected for settings and schema validation because it integrates naturally with FastAPI and keeps API contracts explicit.

## 4. Database Decisions

SQLite was selected over PostgreSQL for the MVP.

The project does not need distributed transactions, concurrent multi-user workloads, advanced indexing, or managed database infrastructure. SQLite provides the right tradeoff for a demo platform:

- Zero external database setup.
- Single-file local persistence.
- Easy Docker usage.
- Simple reset and reproducibility.
- Low infrastructure overhead.
- Fast enough for a fixed mock dataset.

The schema is still modeled cleanly through SQLAlchemy, so moving to PostgreSQL later would mainly involve configuration, migrations, and deployment changes rather than a complete rewrite.

## 5. AI / NLP Design Decisions

MolGenix supports natural-language biomedical queries so users can interact with the prototype in the style of a real AI discovery assistant.

Gemini is integrated as a lightweight NLP layer for target identification and report summarization. The AI layer is intentionally constrained: it receives only the available demo targets and is instructed not to invent new targets.

The keyword fallback exists for reliability.

Reasons for fallback:

- The demo should work without an API key.
- External API failures should not break the core workflow.
- Judges and reviewers should see deterministic behavior.
- All predefined targets must remain discoverable offline.

The fallback is not a replacement for biomedical NLP. It is a reliability mechanism that guarantees every demo target can be identified in controlled scenarios.

## 6. Molecular Pipeline Decisions

Real molecular docking was intentionally not implemented.

Production docking workflows require protein structures, ligand preparation, binding-site configuration, docking engines, compute resources, scoring interpretation, and expert review. Adding that complexity would slow the demo, increase infrastructure requirements, and risk implying scientific validity that the project does not claim.

MolGenix instead uses:

- Pre-seeded molecules.
- Simulated docking scores.
- Simulated ADMET signals.
- Simulated toxicity and filtering flags.
- RDKit-based SMILES parsing and 2D structure rendering.

RDKit is used for visualization and lightweight cheminformatics utilities, not for real discovery claims. The goal is to provide scientifically familiar visuals and ranking behavior while keeping the product fast, reproducible, and honest about its limitations.

## 7. Frontend Decisions

The frontend uses vanilla HTML, CSS, and JavaScript.

React, Vue, Angular, Tailwind, and Bootstrap were intentionally avoided to keep the MVP portable and easy to inspect. This decision reduces setup complexity and makes the interface easier for reviewers to understand without needing a modern frontend toolchain.

Benefits of vanilla frontend implementation:

- No build step required.
- Smaller runtime footprint.
- Easier onboarding for contributors.
- Direct static serving through FastAPI.
- Clear separation between API calls and UI rendering.

The UI is designed as a modern biomedical dashboard. The visual direction emphasizes a premium SaaS feel, clear information hierarchy, smooth interactions, and a research-friendly workflow rather than a flashy AI interface.

## 8. PDF Report Design Decisions

PDF export exists because reports are a natural artifact in scientific and stakeholder workflows. A downloadable report makes the demo feel complete: users can submit a query, inspect molecules, generate a summary, and share an output.

ReportLab was chosen because it supports local PDF generation without external services. It allows the backend to embed molecule diagrams, tables, summaries, ADMET interpretation, methodology, and disclaimers into a deterministic file.

The report layout is publication-inspired:

- Cover page with executive summary.
- Ranked candidate tables.
- Embedded molecule structure diagrams.
- ADMET interpretation.
- Methodology and simulation scope.
- Clear demo-only disclaimer.

The PDF is designed for presentation value and researcher readability, while clearly stating that outputs are simulated.

## 9. Performance and Scalability Tradeoffs

MolGenix avoids advanced infrastructure on purpose.

The MVP does not use:

- Distributed workers.
- GPU inference.
- Message queues.
- External databases.
- Object storage.
- Authentication providers.
- Real docking engines.

These omissions keep startup fast and deployment simple. The current architecture is sufficient for a single-user demo flow and automated tests.

Future scalability paths are still available:

- Replace SQLite with PostgreSQL.
- Add background jobs for report generation.
- Store generated assets in object storage.
- Move AI calls behind a provider abstraction.
- Add caching for molecule and report data.
- Introduce real deployment observability.

The current implementation optimizes for reliability, clarity, and demo speed rather than high-throughput production workloads.

## 10. Security and Authentication Decisions

Authentication was intentionally excluded.

The MVP is a local/demo prototype, not a production application. Adding users, sessions, password handling, OAuth, authorization rules, and account management would add significant complexity without improving the core demonstration.

Current assumptions:

- The app runs in a trusted local or demo environment.
- Data is mock-only.
- There are no private user records.
- There are no real pharmaceutical assets.

Authentication, authorization, audit logs, rate limiting, and secret-management hardening would be required before any production deployment.

## 11. Design System Decisions

The visual system is intended to feel like a modern biotech SaaS product.

Design choices include:

- A refined logo system based on an abstract `M`.
- Dark and light mode support.
- Muted scientific colors instead of saturated gradients.
- Premium typography and restrained spacing.
- Clear molecule cards, target cards, report panels, and modal layouts.
- Smooth transitions and subtle depth effects.

The brand direction is modern, minimal, and credible. The UI should feel suitable for an AI healthcare startup, while remaining transparent that the scientific workflow is simulated.

## 12. Known Limitations

MolGenix has important limitations:

- Outputs are simulated.
- Molecules are pre-seeded.
- Docking scores are mock values.
- ADMET signals are mock values.
- There is no real biomedical validation.
- There is no wet-lab evidence.
- There is no real docking pipeline.
- There is no molecular generation.
- The dataset is limited to 5 targets and 40 molecules.
- Reports are demonstration artifacts, not scientific recommendations.

These limitations are intentional for the MVP. They keep the project honest, reproducible, and appropriate for demo usage.

## 13. Future Improvements

Possible future directions include:

- Real docking engine integration.
- Real molecular generation workflows.
- Protein structure visualization.
- Expanded target and molecule datasets.
- PostgreSQL migration.
- Background workers for long-running jobs.
- Cloud deployment.
- Authentication and role-based access control.
- Multi-target workflows.
- GPU-backed inference.
- Experiment tracking.
- Real dataset ingestion with licensing controls.
- Improved scientific validation workflows.

These improvements should be introduced only with clear product scope and appropriate scientific safeguards.

## 14. Final Engineering Principle

MolGenix prioritizes clarity, educational value, engineering quality, and demo realism over scientific completeness.

The project is strongest when it remains transparent about what is simulated, disciplined about its architecture, and focused on presenting a polished end-to-end prototype without overstating biomedical capability.
