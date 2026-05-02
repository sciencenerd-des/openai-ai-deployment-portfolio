# Project Index

Use this order when linking projects for OpenAI applications or referral conversations.

## 1. Personal-AI

Positioning: Multi-agent deployment platform.

Use it to show:

- Orchestrator-first architecture.
- Specialist agent services.
- Context store / MCP-style memory.
- Web and mobile dashboards.
- Spec-driven development.
- Deployment concerns across services.
- Deployment case study, eval plan, observability plan, and safety/failure-mode analysis.

Completed cleanup:

- Fix unresolved README merge conflict markers.
- Added docs for evals, observability, and safety/failure modes.
- Added OpenAI deployment case study.
- Combined the data-gatherer role into `services/researcher`.
- Combined the coder role into `services/analyst`.
- Removed the legacy standalone `services/data-gatherer` and `services/coder` workspace packages.
- Added `docs/service-consolidation.md` to explain the runtime boundary decision.

Remaining cleanup before sharing:

- Remove generated artifacts or build outputs from public-facing views where possible.

## 2. WalletWatch

Positioning: Codex/spec-driven implementation case.

Use it to show:

- Deterministic spec pack.
- Product requirements, API contracts, data model, QA, and runbook.
- Agent task prompts.
- A workflow for AI coding agents and human review.
- Implemented domain core with event classification, transfer/approval normalization, alert rule dispatch, and spine tests.

Completed cleanup:

- Added `classifyEvent()`, `normalizeTransfer()`, `normalizeApproval()`, and `evaluateAlertRule()`.
- Added focused domain tests for normalization and rule dispatch.
- Added `docs/codex-implementation-case-study.md`.
- Updated the README to state what is implemented versus specified.

## 3. capability-data-annotation-agent

Positioning: Human-in-the-loop startup workflow.

Use it to show:

- Schema-driven labeling.
- Calibration.
- Confidence scoring.
- Human review queue.
- REST/Python usage.
- Exportable labeled datasets.
- Deployment notes, human-review workflow, sample outputs, and label-quality eval cases.

Completed cleanup:

- Replaced aggressive cost/accuracy claims with measured or qualified language.
- Removed freelance pricing language from the main README and supporting docs.
- Added sample eval cases and deployment notes.
- Added human review workflow notes and sample JSONL output.

## 4. Financial_Agents

Positioning: Risk-aware multi-agent decision-support system.

Use it to show:

- Multi-agent workflow separation.
- Verification before action.
- Human approval gates.
- Fail-closed controls.
- Operational runbooks.
- Risk-aware AI deployment pattern for high-stakes workflows.

Completed cleanup:

- Clarified that the project is decision support and workflow research, not financial advice.
- Highlight reliability, auditability, and risk-control design.
- Added an AI deployment case study and risk-control disclaimer.

## 5. India EdTech Use Case

Positioning: India EdTech AI deployment story.

Status: concept/interview note. I did not find a local `AI-Teacher` repo in this workspace.

Use it to show:

- India-specific educational use case.
- Tutor, curriculum, assessment, and doubt-solving workflows.
- Correctness and pedagogical eval concerns.

Recommended cleanup before sharing as a project:

- Create or locate the actual project repo.
- Add a concise EdTech deployment case study.
- Include sample eval cases for correctness, hallucination resistance, and explanation quality.

## 6. task-manager

Positioning: Full-stack app for AI-assisted feature delivery.

Use it to show:

- Practical web app delivery.
- Small feature tasks suitable for Codex workflows.
- Integration, tests, and review loop potential.
- Next.js, Convex, WorkOS, CI, and real application surfaces for small Codex tasks.

Completed cleanup:

- Added `docs/codex-workflow-case-study.md`.
- Added README portfolio framing for Codex-style feature work.
- Added non-interactive Next.js ESLint config.
- Fixed local WorkOS AuthKit component typing so `npm run typecheck` passes.

Maintenance note:

- Regenerate `convex/_generated/*` with `npx convex codegen` after connecting this checkout to a Convex deployment.
