const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const dist = path.join(root, "dist");

fs.mkdirSync(dist, { recursive: true });

const sharedContact = {
  name: "Biswajit Mondal",
  email: "bmondal0000@gmail.com",
  portfolio: "github.com/sciencenerd-des/openai-ai-deployment-portfolio",
};

const cvs = [
  {
    slug: "startups",
    theme: "startups",
    title: "AI Deployment & LLM Systems Builder",
    role: "OpenAI AI Deployment Engineer, Startups - India Remote",
    summary:
      "AI systems builder focused on practical LLM deployment: multi-agent orchestration, human-in-the-loop workflows, eval-driven reliability, review gates, and operational controls. Engineering and audit background with strong instincts for traceability, insufficient-data handling, documentation, and failure-mode analysis. Focused on India-relevant startup use cases across data operations, EdTech, finance workflows, and AI-assisted software delivery.",
    projects: [
      {
        title: "Data Annotation Agent",
        subtitle: "Human-in-the-loop AI workflow",
        bullets: [
          "Built a schema-driven annotation workflow with confidence scoring, calibration, human review, and exportable JSONL outputs.",
          "Added deployment notes, human-review workflow documentation, sample label-quality eval cases, and sample output artifacts.",
          "Positioned the system around startup needs: repeatability, measurable quality, reviewability, and operational readiness.",
          "Demonstrates how a customer workflow can move from AI idea to useful production path.",
        ],
      },
      {
        title: "Personal-AI",
        subtitle: "Multi-agent deployment architecture",
        bullets: [
          "Designed an architecture with orchestrator, researcher service, analyst service, context store, REST APIs, web/mobile surfaces, and deployment documentation.",
          "Consolidated service boundaries by merging data gathering into researcher workflows and coding assistance into analyst workflows.",
          "Added eval, observability, safety, failure-mode, and OpenAI deployment case-study documentation.",
          "Shows judgment around turning a complex agent system into clearer service boundaries and operable deployment units.",
        ],
      },
      {
        title: "Financial_Agents",
        subtitle: "Risk-aware decision-support workflow",
        bullets: [
          "Developed a multi-agent workflow pattern separating perception, drafting, verification, orchestration, and stakeholder translation.",
          "Reframed the project around decision support with approval gates, fail-closed controls, provider-neutral LLM configuration, and runbooks.",
          "Applied audit-style reliability thinking to a workflow where traceability and blocked states matter.",
        ],
      },
      {
        title: "AI-Teacher",
        subtitle: "India EdTech deployment concept",
        bullets: [
          "Framed an India-specific AI tutor workflow around curriculum alignment, doubt solving, assessment, progress tracking, and correctness evals.",
          "Useful as a deployment story where adoption depends on trust, local context, affordability, and measurable learning quality.",
        ],
      },
    ],
    strengths: [
      "Convert ambiguous workflows into AI product architecture.",
      "Design LLM workflows with schemas, evals, confidence thresholds, and human review.",
      "Think in deployment terms: service boundaries, retries, observability, failure states, and user trust.",
      "Translate AI capabilities into India-relevant startup use cases.",
      "Communicate tradeoffs clearly across technical and business audiences.",
    ],
    positioning:
      "I help startup teams convert high-value but messy workflows into deployable LLM products using schemas, evals, confidence thresholds, human review, and operational controls.",
  },
  {
    slug: "codex",
    theme: "codex",
    title: "AI Deployment & AI-Assisted Engineering Workflow Builder",
    role: "OpenAI AI Deployment Engineer, Codex - India",
    summary:
      "AI systems builder focused on Codex-style engineering workflows: spec-driven implementation, coding-agent task prompts, tests, diffs, repair loops, CI, and human review gates. Experience across TypeScript, Python, Next.js, Convex, multi-agent systems, and LLM workflow design. Audit background gives a reliability mindset around traceability, failure modes, documentation, and operational controls.",
    projects: [
      {
        title: "WalletWatch",
        subtitle: "Spec-driven Codex implementation case",
        bullets: [
          "Built a deterministic implementation pack for AI coding agents: requirements, business logic, API contracts, architecture, data model, QA expectations, runbooks, and agent task prompts.",
          "Implemented and tested a focused domain core: event classification, transfer normalization, approval normalization, and alert rule evaluation.",
          "Demonstrated a repeatable Codex workflow: clear spec, small task, generated patch, tests, diff review, and human approval.",
          "Maps directly to Codex adoption work: helping teams make coding agents useful, inspectable, and safe inside the SDLC.",
        ],
      },
      {
        title: "task-manager",
        subtitle: "Full-stack Codex workflow target",
        bullets: [
          "Added a Codex workflow case study to a full-stack Next.js, Convex, and WorkOS task management app.",
          "Added non-interactive Next.js ESLint config and fixed local WorkOS AuthKit component typing so lint and typecheck pass.",
          "Documented safe task boundaries for AI coding agents: small features, generated backend contracts, auth guardrails, TypeScript checks, CI, and review.",
        ],
      },
      {
        title: "Personal-AI",
        subtitle: "Agentic system and service boundary design",
        bullets: [
          "Designed a multi-agent architecture with orchestrator, researcher service, analyst service, context store, dashboards, and deployment documentation.",
          "Consolidated coder and data-gathering responsibilities into clearer service boundaries to reduce runtime complexity.",
          "Added eval, observability, and safety/failure-mode documentation relevant to operating agentic systems.",
        ],
      },
      {
        title: "MiniMythos",
        subtitle: "AI coding workflow research",
        bullets: [
          "Positioned as an AI coding-agent evaluation and repair-loop research direction.",
          "Useful interview evidence for discussing how to evaluate generated code, diagnose failures, and design feedback loops.",
        ],
      },
    ],
    strengths: [
      "Convert loose product requests into agent-ready implementation tasks.",
      "Build Codex adoption workflows around specs, tests, diffs, CI, and human review.",
      "Create reference implementations, demos, guides, and reusable engineering patterns.",
      "Explain when AI coding tools help and when humans must stay in control.",
      "Teach practical workflows through examples, guides, workshops, and hands-on demos.",
    ],
    positioning:
      "I design AI-assisted engineering workflows where coding agents operate inside clear specs, tests, diffs, review loops, CI, and production guardrails.",
  },
];

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderList(items, className = "") {
  return `<ul${className ? ` class="${className}"` : ""}>${items
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("")}</ul>`;
}

function renderProject(project) {
  return `<article class="project">
    <h3>${escapeHtml(project.title)} <span>${escapeHtml(project.subtitle)}</span></h3>
    ${renderList(project.bullets)}
  </article>`;
}

function renderCv(cv) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(sharedContact.name)} - ${escapeHtml(cv.role)}</title>
  <link rel="stylesheet" href="/templates/editorial-cv.css" />
  <script src="https://mcp.figma.com/mcp/html-to-design/capture.js" async></script>
</head>
<body class="${cv.theme}">
  <main class="page">
    <header class="masthead">
      <div>
        <p class="eyebrow">AI Deployment Portfolio</p>
        <h1>${escapeHtml(sharedContact.name)}</h1>
        <p class="title">${escapeHtml(cv.title)}</p>
      </div>
      <address class="contact">
        <div>${escapeHtml(sharedContact.email)}</div>
        <div><a class="portfolio" href="https://${escapeHtml(sharedContact.portfolio)}">${escapeHtml(sharedContact.portfolio)}</a></div>
        <div>India</div>
      </address>
    </header>

    <section class="intro">
      <p class="summary">${escapeHtml(cv.summary)}</p>
      <div class="role-card">
        <p class="role-label">Target Role</p>
        <p class="role">${escapeHtml(cv.role)}</p>
      </div>
    </section>

    <div class="content">
      <section>
        <h2>Selected Project Experience</h2>
        ${cv.projects.map(renderProject).join("")}
      </section>

      <aside>
        <section class="side-section">
          <h2>Relevant Strengths</h2>
          ${renderList(cv.strengths, "strength-list")}
        </section>
        <section class="side-section">
          <h2>Positioning</h2>
          <p class="quote">${escapeHtml(cv.positioning)}</p>
        </section>
      </aside>
    </div>

    <footer class="footer">
      Built for OpenAI application materials. Public portfolio: https://${escapeHtml(sharedContact.portfolio)}
    </footer>
  </main>
</body>
</html>`;
}

for (const cv of cvs) {
  const out = path.join(dist, `biswajit_mondal_openai_${cv.slug}_cv_editorial.html`);
  fs.writeFileSync(out, renderCv(cv));
  console.log(out);
}
