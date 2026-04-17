# ADR 0001 — Monorepo for the portfolio arc

Status: Accepted
Date: 2026-04-16

## Context

The portfolio comprises four related projects, each a non-trivial deliverable on its own. A reader should be able to follow the arc from Project 01 through Project 04 without context-switching.

Cross-project assets — architecture decision records, glossary, talking points, reusable OpenTofu modules, bootstrap scripts — are inherently shared. Versioning them across four independent repositories would duplicate effort and drift over time.

## Decision

Keep all four projects in a single monorepo. Top-level structure:

```
sre-platform/
├── shared/            # cross-project knowledge and modules
├── project-01-*/
├── project-02-*/
├── project-03-*/
└── project-04-*/
```

Each project directory is self-contained: its own `README`, infrastructure, application code, and tests.

## Consequences

**Upside**

- A single URL to share with recruiters; one landing README explains the arc.
- `shared/` is a first-class concept — reuse is obvious and enforced by directory layout.
- Dependencies across projects (Project 02 consumes Project 01's Platform API) read clearly in one tree.
- Atomic changes across projects are possible when they're warranted.

**Downside**

- GitHub stars, forks, and issue counts are per-repository, so each project does not accumulate independent social proof.
- A future reader interested in only one project downloads the whole tree. Acceptable given the small size.

## Alternatives considered

- **Multiple repositories, one per project.** Rejected because `shared/` cannot cleanly live as git submodules (the UX is poor) and the arc becomes harder to follow.
- **Single repo, single project.** Rejected because the portfolio narrative explicitly spans reliability, platform engineering, GitOps, and agentic operations — one project cannot hold the story.
