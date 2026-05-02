# Interview Talking Points

## Core Positioning

My path is non-traditional, but my portfolio shows relevant deployment work: building AI workflows, designing agent systems, creating evals, using AI coding tools, writing specs, and adding reliability controls.

## Story 1 - Personal-AI

Question: Tell us about an AI system you designed.

Answer structure:

- User request enters an orchestrator.
- Orchestrator routes work to two practical worker boundaries: researcher and analyst.
- Services use context storage and structured interfaces.
- Results return through a controlled API boundary.
- Reliability concerns include retries, health checks, observability, evals, and human review where needed.

Key point:

An AI system is not just a prompt. It needs service boundaries, state, failure handling, and a deployment model. I also learned that too many agents can make a system harder to operate, so I consolidated data gathering into researcher workflows and coding assistance into analyst workflows.

## Story 2 - WalletWatch

Question: How would you use Codex safely?

Answer structure:

- Start with a clear spec.
- Break work into a small issue.
- Give Codex only relevant context.
- Ask for a patch.
- Run tests and type checks.
- Review the diff.
- Feed failures back into the repair loop.
- Merge only after CI and human approval.

Key point:

Codex should raise engineering leverage without removing engineering responsibility.

Concrete example:

WalletWatch shows the spec-pack side; task-manager shows the real full-stack app side where lint, typecheck, generated backend types, and human review become the adoption loop.

## Story 3 - Data Annotation Agent

Question: How would you help a startup deploy AI?

Answer structure:

- Understand the workflow and success metric.
- Define schema and output contract.
- Run calibration samples.
- Add confidence scoring.
- Route uncertain cases to human review.
- Produce quality reports.
- Export data in usable formats.

Key point:

Startups need useful deployed workflows, not just demos.

Concrete example:

The Data Annotation Agent has deployment notes, human-review workflow notes, label-quality eval cases, and sample JSONL output.

## Story 4 - India EdTech Use Case

Question: How do you adapt AI to Indian markets?

Answer structure:

- Start from the learner context, exam context, and language/context constraints.
- Separate curriculum planning, tutoring, assessment, and doubt solving.
- Evaluate factual correctness and explanation quality.
- Add safeguards around hallucination and overconfident wrong answers.

Key point:

Indian AI deployment needs local workflow understanding, cost sensitivity, and domain-specific evaluation.

## Story 5 - Audit Background

Question: Why should we consider a non-traditional candidate?

Answer:

AI deployment is not only about making demos work. It is about reliability, traceability, failure handling, documentation, controls, and helping real users trust the system. My audit background trained those instincts, and my AI projects show how I apply them to LLM systems and coding workflows.

Concrete example:

In Financial_Agents, I frame the system as decision support, not financial advice. I also removed required provider-specific LLM key coupling and made the configuration provider-neutral, which is the kind of deployment cleanup customers often need.

## Questions to Ask OpenAI

- What are the most common failure modes customers hit when moving from prototype to production?
- For Codex adoption, what separates teams that get durable value from teams that only use it experimentally?
- How does the deployment team feed customer workflow learnings back into product and model teams?
- What does success look like in the first 90 days for this role?
