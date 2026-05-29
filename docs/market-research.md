# GST / Taxation Market Research & Feature Specs

> Research backing the Bharat Doc Intelligence roadmap. Sources: tax-industry
> press, vendor docs, and primary GSTN / NIC e-Invoice API specifications.
> Compiled May 2026. Citations are inline as footnote-style links.

**Contents**
1. [Problem landscape](#1-problem-landscape)
2. [Competitive / feature landscape](#2-competitive--feature-landscape)
3. [White space & strategic positioning](#3-white-space--strategic-positioning)
4. [GSTN / NIC API reference (for verification & reconciliation features)](#4-gstn--nic-api-reference)
5. [Detailed feature specs](#5-detailed-feature-specs)
6. [Reconciliation feature — implementable subtasks](#6-reconciliation-feature--implementable-subtasks)
7. [Prioritized backlog](#7-prioritized-backlog)

---

## 1. Problem landscape

GST compliance is a monthly, high-stakes chore for ~15M registrants, and 2025–26
rule changes have sharply increased the burden.

- **Time sink.** Micro-enterprises spend ~28.6 hrs/month on GST work, small firms
  ~21.4, medium ~15.7; teams on disconnected tools lose 20–40 hrs/month. GST eats
  15–25% of an SME's operational time.[^binary][^wowhow]
- **Reconciliation is the #1 pain.** GSTR-2B freezes on the 14th; buyers get ~6 days
  to match it against their purchase register, and the **Invoice Management System
  (IMS)** (live since 14 Oct 2024) forces an Accept/Reject/Pending decision per
  invoice.[^cnbc][^batchwise]
- **Auto-notices fire on mismatches.** Rule 88C flags GSTR-1 vs GSTR-3B gaps; Rule
  88D auto-issues DRC-01C and can block GSTR-1 if ITC claimed exceeds GSTR-2B by
  ₹1 lakh / 20%. Since Jan 2026 the portal blocks filing on a 2B mismatch; GSTR-3B
  is hard-locked from GSTR-1 (July 2025).[^a2z][^proanalyser]
- **Cash-flow risk.** Blocked ITC freezes working capital + 18% interest; recovery
  in as little as 7 days.[^cnbc]
- **More SMEs pulled in.** e-invoicing mandatory at ≥₹5 cr turnover (threshold
  expected to fall toward ₹2 cr), with a 30-day IRN upload limit at ≥₹10 cr — late
  invoices become invalid and break ITC.[^proanalyser]
- **Cross-portal scrutiny.** GST data is matched against Form 26AS / AIS, e-way
  bills, and TCS.[^taxguru-notices]

**Recurring task chain (the product surface):** invoice capture → GSTIN/IRN
validation → GSTR-2B ↔ purchase-register reconciliation → ITC eligibility & risk
scoring → return prep (GSTR-1/3B) → vendor follow-up → notice response → annual
reconciliation (GSTR-9/9C).

## 2. Competitive / feature landscape

| Product | Type | GST strengths | Gaps |
|---|---|---|---|
| ClearTax | GSP, AI-forward | Fast recon (claims 6,000 inv/min), GSTN API, e-invoicing, ITC-at-risk dashboard | Paid; CA/enterprise-oriented |
| Zoho Books | GSP, cloud | Direct GSTR-1/3B filing, auto 2B recon + mismatch flags, bank feeds; free <₹50L | Per-GSTIN add-on; weak offline |
| TallyPrime | ASP, desktop | GST embedded in entries, multi-GSTIN, 2A/2B recon, e-invoice/IRN | Desktop-first, manual bank import, paid TSS |
| Vyapar / myBillBook | Billing apps | Fast WhatsApp GST billing, offline | **Report-only** — no portal filing, basic recon |
| BUSY / ExpressGST / Gen / Saral | Mid-market | GSTIN/HSN validation, JSON gen, bulk filing | Mostly accountant-facing |
| GST Notice AI, Suvit, AI Accountant, Nanonets | Point AI tools | Notice OCR + AI reply drafting w/ CGST citations, vision PDF extraction, fuzzy 2B matching, automated vendor follow-ups | Narrow, single-workflow |

Sources: [^aidukan] [^pkc] [^g2] [^gstnoticeai] [^aiaccountant].

## 3. White space & strategic positioning

1. **Multimodal capture for messy Indian reality** — thermal prints, handwritten
   bills, WhatsApp photos, regional-language invoices. OCR+NLP hits 95%+ and cuts
   data entry 70–80%.[^cleartaxadv][^wowhow] *This is Bharat Doc Intelligence's wedge.*
2. **Agentic ITC reconciliation + autonomous vendor chasing** — detect a missing
   2B invoice → score supplier risk → draft/send follow-up → update ITC ledger.[^linkedin]
3. **Notice triage & reply drafting** (DRC-01/ASMT-10) with RAG-grounded CGST
   citations + human sign-off.[^gstnoticeai][^icai]
4. **Validation-at-intake** — GSTIN status, IRN/QR verification, HSN-rate checks
   before posting.[^aiaccountant]

**Architecture validation.** Industry consensus: *"use automation — not GenAI —
for rule-based compliance tasks where determinism is required; keep a
human-in-the-loop; ground outputs in source (RAG); LLMs have a training
cutoff."*[^taxguru-ai] Bharat Doc Intelligence's "model reads, deterministic
Python judges" design **is** the recommended pattern. Lead with this.

---

## 4. GSTN / NIC API reference

> **Access reality.** GSTN production APIs are not open: you connect either as a
> licensed **GSP** (GST Suvidha Provider) over MPLS, or — more practically for a
> demo — through a **GSP/ASP reseller** (Sandbox/Quicko, Masters India, Vayana,
> Cygnet) that exposes clean REST + an API key.[^gsp] The **NIC e-Invoice system**
> has an open **sandbox** with full public docs.[^nicsandbox] Design the feature
> behind a `GstnClient` interface with a **mock implementation** (consistent with
> our zero-key mock mode) and a pluggable live provider.

### 4.1 NIC e-Invoice (IRP) — IRN & GSTIN verification

Sandbox base URLs: `https://einv1api.gstsandbox.nic.in/`, `https://einv2api.gstsandbox.nic.in/`.[^nicendpoints]

| Purpose | Method | Endpoint |
|---|---|---|
| Authenticate | POST | `eivital/v1.04/auth` |
| Get GSTIN details | GET | `eivital/v1.04/Master/gstin/{gstin}` |
| Get IRN details (verify) | GET | `eicore/v1.03/Invoice/irn/{irn}` |
| Get IRN by doc details | GET | `eicore/v1.03/Invoice/irnbydocdetails?doctype=&docnum=&docdate=` |

**Auth model.**[^nicauth] Headers `client_id`, `client_secret`, `Gstin`. Payload
`{UserName, Password, AppKey}` is Base64-encoded then RSA-encrypted with the
e-Invoice public key. Response returns `AuthToken` + `Sek` (AES-256 session key);
token valid 360 min (60 on sandbox). Subsequent calls send `AuthToken` + `Gstin` +
`user_name` headers; response `Data` is Base64 + AES-encrypted with `Sek`.

**Get IRN details response (after decrypt):**[^nicirn] `AckNo`, `AckDt`,
`Irn`, `SignedInvoice` (JWT/JWS, SHA256RSA), `SignedQRCode` (JWT/JWS),
`Status` (`ACT`/`CNL`/`REJ`), `EwbNo`/`EwbDt`. **Note:** retrievable only within
**3 days** of IRN generation.

**Offline IRN check (no API needed).** Per the spec, the IRN is the
`SHA256` hash of supplier `Gstin`, `DocDtls.No`, `DocDtls.Typ`, and the financial
year of `DocDtls.Dt`.[^nicirn] We can therefore **recompute and compare** the IRN
fully offline:

```python
import hashlib

def expected_irn(gstin: str, doc_no: str, doc_type: str, fin_year: str) -> str:
    # doc_type ∈ {INV, CRN, DBN}; fin_year like "2025-26"
    payload = f"{gstin}{doc_no}{doc_type}{fin_year}"   # ⚠ confirm exact concatenation/separators against NIC validation doc
    return hashlib.sha256(payload.encode()).hexdigest()
```

> ⚠ The exact string assembly (separators, case, FY format) must be confirmed
> against the NIC validations page before relying on it for hard rejects; until
> then treat a mismatch as a *warning*, not an *error*.

### 4.2 GSTIN status verification (GSP reseller — Sandbox/Quicko shown)

`POST https://api.sandbox.co.in/gst/compliance/public/gstin/search` (also
`/gstin/verify`). Headers: `x-api-key`, `authorization` (JWT), `x-api-version`.
Body: `{"gstin": "29ABCDE1234F1Z5"}`.[^sandboxgstin]

Key response fields: `sts` (status — `Active`/`Cancelled`), `lgnm` (legal name),
`tradeNam`, `ctb` (constitution), `dty` (taxpayer type), `rgdt` (registration
date), `cxdt` (cancellation date), `nba` (nature of business), `pradr`/`adadr`
(addresses), `einvoiceStatus`, `lstupddt`. Masters India offers analogous
`gstinbypan` and `searchlegalname` endpoints.[^masters]

This complements our existing **offline GSTIN checksum** (`app/validators.py`):
checksum proves *well-formed*; the API proves *real & active*.

### 4.3 GSTR-2B / 2A fetch (taxpayer-authenticated, GSP)

Session model: **Generate OTP → Verify OTP → 6-hour session token** (Refresh
Session for long pulls).[^sandbox2a] GSTR-2B is paginated by `file_number`
(1..`fc`) when `status_cd = 3`.[^sandbox2b] Manual fallback: download
JSON/Excel from the portal (Services → Returns → GSTR-2B; >1000 docs require file
download).[^portal2b]

**GSTR-2B JSON shape (per supplier):**[^vayana] sections `b2b`, `b2ba`, `cdnr`,
`cdnra`, `ecom`, `impg`, …; each supplier block has `ctin` (counterparty GSTIN),
`trdnm`, `supprd` (supplier period), `supfildt` (filing date), and `inv[]` with
`items[]` = `{num, rt, txval, igst, cgst, sgst, cess}`.

**2B generation window & IMS semantics:**[^batchwise] 2B captures supplier docs
filed 14th-of-prev-month → 13th-of-current; generated on the 14th. IMS actions:
*Accept* (or deemed-accept on no action) → ITC-eligible; *Reject* → ITC-rejected;
*Pending* → excluded this month (subject to the Section 16(4) cut-off of 30 Nov
following FY end). ITC eligibility is matched against **2B (static), not 2A
(dynamic)**.

---

## 5. Detailed feature specs

Each spec is written to drop into the existing repo (`app/schemas.py`,
`validators.py`, `agent.py`, `pipeline.py`) and to keep the mock-first, eval-gated
discipline.

### Spec A — Live GSTIN verification (extends offline checksum)

- **Problem.** A checksum-valid GSTIN can still be cancelled, suspended, or belong
  to a different legal name than printed → ghost-vendor ITC risk.
- **User story.** *As a buyer, when I scan a supplier invoice, I want to know the
  GSTIN is active and the legal name matches, so I don't claim ITC against a ghost
  vendor.*
- **Inputs.** `gstin: str`, optional `printed_legal_name: str`.
- **Outputs.** New `GstinStatus` model: `{gstin, well_formed, registered, status,
  legal_name, trade_name, registration_date, cancellation_date, name_match: bool,
  source: "mock"|"live"}`.
- **External API.** §4.2 GSP search/verify; behind `GstnClient.get_gstin(gstin)`.
- **Logic.** (1) run existing offline `validate_gstin`; if malformed, short-circuit.
  (2) call `GstnClient`; in mock mode return canned statuses keyed by GSTIN
  prefix. (3) fuzzy-compare `printed_legal_name` vs `lgnm` (token-set ratio ≥ 0.8).
- **Agents-SDK.** Upgrade the existing `validate_gstin` function tool to optionally
  return live status, so the extraction agent can self-flag a cancelled GSTIN.
- **Anomalies emitted.** `gstin_cancelled` (error), `gstin_name_mismatch` (warning),
  `gstin_unverified` (info, when live lookup unavailable).
- **Acceptance.** Cancelled-GSTIN fixture → `gstin_cancelled`; name mismatch →
  warning; offline/no-key → graceful `gstin_unverified`, never crash.
- **Tests/eval.** Mock `GstnClient` fixtures; add 3 cases to `evals/dataset`.
- **Effort.** M (½–1 day incl. mock client).

### Spec B — IRN / QR verification

- **Problem.** B2B invoices ≥ threshold must carry a valid IRN + signed QR; a
  missing/forged IRN means the buyer's ITC is at risk.
- **User story.** *As a buyer, I want the scanned invoice's IRN/QR validated so I
  know it was genuinely registered on the IRP.*
- **Inputs.** Either a decoded `signed_qr` (JWT) or `(gstin, doc_no, doc_type,
  doc_date)` + optional printed `irn`.
- **Outputs.** `IrnStatus: {irn, recomputed_irn, irn_matches: bool, qr_signature_valid:
  bool|None, irp_status: "ACT"|"CNL"|"REJ"|None, source}`.
- **Logic.** (1) **offline**: recompute IRN (§4.1) and compare to printed; (2) if a
  signed QR is present, verify the JWS signature against NIC's public cert
  (offline once the cert is bundled); (3) **optional live**: `Get IRN details`
  within the 3-day window for authoritative `Status`.
- **Anomalies.** `irn_missing` (warning for B2B over threshold), `irn_mismatch`
  (warning → error once concatenation confirmed), `irn_cancelled` (error).
- **Acceptance.** Recomputed IRN matches a known-good fixture; tampered doc_no →
  `irn_mismatch`.
- **Effort.** M; the offline recomputation + QR-signature path is the high-value,
  zero-dependency core.

### Spec C — ITC eligibility & risk scoring

- **Problem.** Even a correctly-filed invoice may be ITC-ineligible (S.17(5)
  blocked credits) or risky (supplier files late). Buyers need a per-invoice ITC
  verdict, not just extraction.
- **User story.** *As a buyer, I want each purchase scored "claim now / defer /
  block" with a reason, so I file a safe GSTR-3B.*
- **Inputs.** `ExtractedInvoice` + reconciliation match state (Spec/section 6) +
  optional supplier filing history.
- **Outputs.** `ItcAssessment: {eligible: bool, verdict: "claim"|"defer"|"block",
  risk: 0..1, reasons: list[str]}`.
- **Logic (deterministic).**
  - **Block** if HSN/category in S.17(5) blocked list (motor vehicles, personal
    use, food/canteen, etc.) or `igst+cgst+sgst == 0`.
  - **Defer** if in purchase register but not in 2B (supplier hasn't filed) or 2B
    `supfildt` is late.
  - **Claim** if matched in 2B with values within tolerance.
  - Risk = weighted blend of supplier on-time-filing rate + mismatch severity.
- **Anomalies/links.** Reuses `Anomaly`; feeds the confidence meter.
- **Effort.** M; pure-Python, highly testable, strong eval target.

### Spec D — Agentic vendor follow-up (second agent + handoff)

- **Problem.** "In register, not in 2B" invoices = ITC leakage; chasing suppliers
  is manual.
- **User story.** *As a buyer, for every unmatched purchase I want a drafted
  supplier email (Day 7 reminder → Day 14 escalation → Day 20 "ITC at risk"),
  queued for my approval.*
- **Design.** A `FollowupAgent` (Agents SDK handoff from the recon step) that takes
  the unmatched set + supplier contacts and produces draft emails; **human-in-the-
  loop**: drafts are queued, never auto-sent. Cadence per [^aiaccountant].
- **Outputs.** `list[DraftEmail]` with severity-tiered templates + the specific
  missing invoices.
- **Effort.** M; great showcase of Agents SDK handoffs + HITL.

### Spec E — Notice triage & reply drafting (stretch)

- **Problem.** DRC-01C / ASMT-10 notices are now routine and time-pressured.
- **Design.** Vision OCR of the notice (already have) → classify type → **RAG** over
  a bundled CGST Act / circulars corpus → draft a reply with citations → CA
  reviews/edits/signs. Strictly HITL; verify every citation.[^gstnoticeai][^taxguru-ai]
- **Effort.** L; defer until A–D land. Highest regulatory-risk surface.

---

## 6. Reconciliation feature — implementable subtasks

The flagship feature: match the **purchase register** against **GSTR-2B** and
produce a per-invoice IMS decision + ITC verdict. Built mock-first so it runs
with no GSTN access.

**Data model (add to `app/schemas.py`).**

```python
class PurchaseLine(BaseModel):
    supplier_gstin: str
    invoice_number: str
    invoice_date: str          # ISO
    taxable_value: float
    igst: float = 0; cgst: float = 0; sgst: float = 0; cess: float = 0

class Gstr2bLine(BaseModel):
    ctin: str                  # counterparty (supplier) GSTIN
    invoice_number: str
    invoice_date: str
    taxable_value: float
    igst: float = 0; cgst: float = 0; sgst: float = 0; cess: float = 0
    supplier_filing_date: str | None = None   # supfildt
    section: str = "b2b"       # b2b | cdnr | ...

MatchStatus = Literal["matched", "in_2b_not_register",
                      "in_register_not_2b", "value_mismatch_rounding",
                      "value_mismatch_material"]

class ReconMatch(BaseModel):
    status: MatchStatus
    ims_action: Literal["accept", "reject", "pending", "none"]
    register_line: PurchaseLine | None = None
    gstr2b_line: Gstr2bLine | None = None
    deltas: dict[str, float] = {}
    itc: "ItcAssessment | None" = None

class ReconReport(BaseModel):
    period: str                # "2026-04"
    matches: list[ReconMatch]
    summary: dict[str, float]  # counts + claimable/deferred/blocked ITC totals
```

**Subtasks** (each independently shippable, mock-first, with tests + an eval slice):

| ID | Subtask | Scope / definition of done | Deps |
|----|---------|----------------------------|------|
| **R1** | **Schemas + fixtures** | Add the models above; build `mock` 2B + register fixtures incl. each match category. DoD: models import, fixtures validate. | — |
| **R2** | **Parsers / normalizers** | Parse GSTR-2B JSON (§4.3 shape) → `Gstr2bLine[]`; parse a purchase-register CSV/Excel → `PurchaseLine[]`. Normalize invoice numbers (strip leading zeros, case, `/`-`-`), dates → ISO, round money to 2dp. DoD: golden-file tests. | R1 |
| **R3** | **Tier-1 exact matcher** | Key = `(normalized_gstin, normalized_invno, period)`; exact value compare within ₹1 tolerance → `matched`. Emit unmatched pools both directions. DoD: unit tests on fixtures. | R2 |
| **R4** | **Tier-2 fuzzy matcher** | For leftovers, fuzzy-match on invoice no. (Levenshtein/token ratio) + date proximity (±N days) + value proximity; classify `value_mismatch_rounding` (≤₹1) vs `value_mismatch_material`. DoD: precision/recall measured on a labelled fuzzy set. | R3 |
| **R5** | **IMS decision engine** | Map each match to `ims_action` per [§4.3]: matched→accept; in-register-not-2B→pending+defer; material mismatch→reject; rounding→accept. DoD: decision table fully covered by tests. | R3 |
| **R6** | **ITC assessment** (Spec C) | Attach `ItcAssessment` to each match; compute period totals (claimable / deferred / blocked). DoD: totals reconcile in tests. | R5 |
| **R7** | **API + UI** | `POST /api/reconcile` (2B file + register file) → `ReconReport`; add a "Reconciliation" tab to `web/index.html` (matched/mismatch/missing buckets, ITC totals, per-row IMS action). DoD: endpoint + mock-mode UI works. | R5 |
| **R8** | **Eval harness slice** | Labelled recon dataset (expected match status per pair); extend `evals/run_evals.py` with match-accuracy + ITC-total error; wire into CI gate. DoD: CI fails on regression. | R4, R6 |
| **R9** | **GSP live adapter** (optional) | Implement `GstnClient` live path: OTP session (§4.3) + 2B pull; feature-flagged, mock remains default. DoD: interface parity with mock. | R2 |

**Edge cases to cover (from [^batchwise], [^aiaccountant]):** late supplier
filing crossing the 2B window; credit/debit notes (`cdnr`) reducing ITC; RCM
supplies (never in 2B — assess separately); amendments (`b2ba`/`cdnra`) linking to
originals; duplicate invoice numbers across suppliers; Section 16(4) 30-Nov
cut-off for pending items.

---

## 7. Prioritized backlog

| # | Item | Spec / subtasks | Effort |
|---|------|------|--------|
| P0 | GSTR-2B ↔ register reconciliation | §6 R1–R8 | L (sum of M/S) |
| P0 | ITC risk scoring | Spec C / R6 | M |
| P1 | Live GSTIN verification | Spec A | M |
| P1 | IRN/QR verification (offline core) | Spec B | M |
| P1 | Regional-language extraction eval set | (roadmap) | S |
| P2 | Agentic vendor follow-up | Spec D | M |
| P2 | GSTR-1 vs 3B pre-file mismatch check | (derive from recon) | M |
| P3 | Notice triage + RAG reply | Spec E | L |

**Sequencing:** R1→R6 (the deterministic recon + ITC core, mock-first) is the
highest-value, lowest-risk path and showcases the "model reads, code judges"
thesis. Specs A/B slot in as Agents-SDK tools. D and E demonstrate handoffs and
RAG once the core is solid.

---

### Sources

[^binary]: Binary Semantics — SME GST compliance time stats. https://www.binarysemantics.com/blogs/start-ups-and-smes-gst-compliance-in-india-growing-pains-tech-levers-the-future-ahead/
[^wowhow]: WOWHOW — AI for Indian businesses: GST/tax automation. https://wowhow.cloud/blogs/ai-for-indian-businesses-gst-tax-compliance-automation
[^cnbc]: CNBC-TV18 — GST's invoice vision hits reconciliation wall. https://www.cnbctv18.com/economy/exclusive-i-gsts-grand-invoice-vision-hits-reconciliation-wall-taxpayers-grapple-with-compliance-overload-19610578.htm
[^a2z]: A2Z Taxcorp — "GST has a success problem" (Rule 88D, portal outage). https://a2ztaxcorp.net/gst-has-a-success-problem-experts-flag-next-big-challenge-for-tax-reform/
[^proanalyser]: ProAnalyser — GST Compliance 2025 (hard-lock, e-invoicing, ISD, MFA). https://proanalyser.in/gst-compliance-2025/
[^taxguru-notices]: TaxGuru — Prevent GST notices with monthly reconciliation. https://taxguru.in/goods-and-service-tax/prevent-gst-notices-monthly-reconciliation.html
[^taxguru-ai]: TaxGuru — Harnessing AI in modern GST practice (automation vs GenAI, HITL, RAG). https://taxguru.in/goods-and-service-tax/smarter-safer-sharper-harnessing-artificial-intelligence-modern-gst-practice.html
[^linkedin]: N. Anand — Integrating Agentic AI into India's indirect tax ecosystem. https://www.linkedin.com/pulse/integrating-agentic-ai-indias-indirect-tax-ecosystem-nikhil-anand-bhicc
[^cleartaxadv]: ClearTax Advisors — AI in tax compliance automation (India 2026). https://cleartaxadvisors.in/ai-in-tax-compliance-automation/
[^aiaccountant]: AI Accountant — AP automation with GST compliance (recon, follow-up cadence, edge cases). https://www.aiaccountant.com/blog/ap-automation-gst-compliance-india
[^icai]: ICAI — GST Practice Automation (GST-GPT). https://ai.icai.org/usecases_details.php?id=165
[^gstnoticeai]: GST Notice AI — notice OCR + AI reply drafting. https://gstnoticeai.com/
[^aidukan]: AiDukan — Best GST software in India 2026 (feature matrix). https://aidukan.in/best-software-for-gst-india/
[^pkc]: PKC India — Best accounting software for small business in India 2026. https://www.pkcindia.com/blogs/best-accounting-software-for-small-businesses-in-india-comparison-pricing/
[^g2]: G2 — Zoho Books vs Tally vs Vyapar. https://www.g2.com/articles/zoho-books-vs-tally-vs-vyapar
[^gsp]: GSTN — GSP Implementation Framework v3.0. https://www.gstn.org.in/assets/mainDashboard/Pdf/GSP_Implementation_Framework_V_3.0.pdf
[^nicsandbox]: NIC e-Invoice API Developer Portal (sandbox). https://einv-apisandbox.nic.in/
[^nicendpoints]: NIC e-Invoice — API end points. https://einv-apisandbox.nic.in/einvapiclient/EncDesc/ApiEndsPoint.aspx
[^nicauth]: NIC e-Invoice — Authentication (v1.04). https://einv-apisandbox.nic.in/version1.04/authentication.html
[^nicirn]: NIC e-Invoice — Get IRN Details (v1.03). https://einv-apisandbox.nic.in/version1.03/get-eInvoicedetails.html
[^sandboxgstin]: Sandbox (Quicko) — Search GSTIN API. https://sandbox-docs.readme.io/reference/search-gstin-api
[^masters]: Masters India — GSTIN verification API docs. https://docs.mastersindia.co/gst-verification-api/gstin-search-by-pan-v2
[^sandbox2a]: Sandbox — GSTR-2A overview (OTP session model). https://developer.sandbox.co.in/api-reference/gst/compliance/guides/taxpayer/gstr-2a/overview
[^sandbox2b]: Sandbox — GSTR-2B Document API. https://sandbox-docs.readme.io/reference/gstr-2b-api
[^vayana]: Vayana — GSTR-2B download API (JSON shape). https://docs.enriched-api.vayana.com/routes/basic/gstn/apis/returns/Gstr-Download-Lite-Api/gstr-2b/
[^portal2b]: GST portal — View/download GSTR-2B user guide. https://tutorial.gst.gov.in/userguide/returns/Manual_gstr2b.htm
[^batchwise]: Batchwise — GSTR-2A vs 2B reconciliation + IMS walkthrough (FY 2025-26). https://batchwise.ai/gst/gstr-2a-vs-2b-reconciliation/
