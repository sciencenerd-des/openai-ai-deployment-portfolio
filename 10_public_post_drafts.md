# Public Post Drafts

## Post 1 - How I Use AI Coding Agents Safely

Working with AI coding agents is not just about asking for code faster. The workflow matters more than the prompt.

The pattern I use:

1. Start with a small issue.
2. Provide only the relevant files, specs, and constraints.
3. Ask for a focused diff.
4. Run tests, type checks, and linting.
5. Review the diff like a human engineer wrote it.
6. Feed failures back with logs and exact constraints.
7. Merge only after human review.

The important part is keeping engineering responsibility intact. A coding agent should increase leverage, not remove review.

In my WalletWatch project, I used a spec-first structure: product requirements, API contracts, data model, QA expectations, runbook, and agent task prompts. In a full-stack task-manager app, the same idea becomes practical: small feature request, generated patch, TypeScript check, lint, backend contract review, and human approval.

My rule: if a task cannot be reviewed clearly, it is too large for an AI coding agent.

## Post 2 - From AI Demo to Deployed Workflow

Most AI demos fail at the same point: the model output looks impressive, but the workflow around it is not reliable enough to operate.

A deployed AI workflow needs more than a prompt:

- Input and output contracts.
- Evals.
- Confidence thresholds.
- Human review for uncertain cases.
- Failure states.
- Observability.
- Cost and latency awareness.
- Clear ownership of what the system can and cannot do.

I have been applying this pattern across portfolio projects:

- Data Annotation Agent: schema-driven labeling, confidence scoring, review queue, eval cases, and JSONL exports.
- Personal-AI: orchestrator, researcher service, analyst service, context store, eval plan, observability notes, and failure-mode analysis.
- Financial_Agents: separation of generation, verification, approval, and fail-closed controls.

The lesson is simple: AI deployment is not only about making a model answer. It is about making the workflow inspectable, repeatable, and safe enough for real users.

That is where I want to focus: turning AI demos into reliable deployed workflows.
