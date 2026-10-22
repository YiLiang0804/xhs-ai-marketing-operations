# Evaluation and limitations

**Purpose:** Separate what the automated checks establish from business outcomes that still need a real pilot. Read this to assess the evidence and its limits.

[Back to the project overview](../README.md) · [Next: walkthrough and interview explanation](WALKTHROUGH.md)

## Automated acceptance checks

Run `python -m unittest discover -s tests -v`. Checks cover:

| Area | Acceptance condition |
|---|---|
| Reproducibility | Identical fixtures and ledger produce identical outputs |
| Deduplication | Duplicate IDs and whitespace-normalized exact messages do not add actions |
| Explainability | Each priority score equals the sum of visible rule contributions |
| Missing information | A missing degree goal or timeline remains missing and requests clarification |
| Lifecycle | Closed, paused and handed-off inquiries are excluded from the review queue |
| Permission | A numeric score does not override missing follow-up permission |
| Human gate | Baseline action manifest is empty; eligible items require explicit approval |
| Daily allowance | A saved approval consumes the remaining slot across subsequent runs |
| Repeat-safe approval (idempotency) | Repeating an approval does not consume another slot, including on a later date |
| Public sample boundary | Unlabeled inputs are rejected; all bundled fixtures are synthetic |
| Visible-feed discovery | Supplied context and service fit are checked; a sparse profile alone does not reject a detailed request |
| Cross-run history | Previous post or author contact prevents another planned contact |
| Recipient identity | A liker does not inherit the original author's background |
| Visible result | A click or cleared text box alone cannot verify a comment; a like is checked separately |
| Unknown delivery | An unresolved send is not made retryable |
| Recovery recording | Reservation, submission, acknowledged execution and observations stay distinct |
| Recovery preservation | Consumed allowance, stop/interlock flags, completed history and deadline remain preserved |
| Full-volume public backend | All 606 leads, 1,771 events, 39 runs and 95 profiles are loaded, rather than only a preview |
| Public table relationships | Unique synthetic keys and valid event-to-lead/run and optional lead-to-mentor references |

These are application checks, not an evaluation of an LLM's reasoning or platform-policy compliance. Fields such as `followup_permission`, post observations and target-verification signals are supplied in fixtures; the prototype does not infer or independently observe them. Historical records report 20 isolated checks in a different suite; the current test command reports this release's count.

## Content review rubric for a future pilot

Use two human reviewers when feasible. Score each dimension 0 (unacceptable), 1 (needs editing), or 2 (ready). A factual error or invented credential is a blocking failure regardless of total score.

1. **Factual fidelity:** no invented speaker, institution, event time, availability or outcome.
2. **Audience relevance:** addresses one concrete question for the intended Bio audience.
3. **Voice:** conversational English public adaptation, readable and restrained; not a reproduction of private account copy.
4. **Next-step clarity:** a low-pressure call to action (CTA) that does not imply a guaranteed service or result.
5. **Handoff usefulness:** stated goal, timeline, missing fields and next step remain visible.

The three included drafts have not been independently rated. Their presence does not imply a measured quality score. Historical aggregate counts, full-volume synthetic tables and small regression fixtures are separately labeled throughout the report.

## Before/after study design — proposed, not performed

Use the same authorized, de-identified inquiry set for a manual process and an assisted process. Alternate the order or split the set to reduce practice effects. Record reviewer experience and actual sample size.

| Measure | Definition / denominator | Caveat |
|---|---|---|
| Review effort | Median minutes per completed inquiry or draft, including correction time | Exclude idle time consistently; do not substitute script runtime |
| Draft acceptance | Accepted without substantive changes / reviewed drafts | Report count as well as rate |
| Unsupported claims | Drafts with at least one unsupported claim / reviewed drafts | Requires human fact checking |
| Handoff completeness | Handoffs with all required known fields or explicit unknowns / reviewed handoffs | Missing data is not an invitation to fabricate |
| Missed follow-up | Eligible follow-ups past a defined due date / eligible follow-ups due | Needs real timestamps and an agreed follow-up policy |
| Model cost | Actual API spend / reviewed item | Only applicable after a real integration |

Leads, consultations and signed contracts are different funnel stages. Any eventual conversion analysis would need clear attribution windows and controls for topic, distribution, audience and seasonality. This prototype contains no revenue attribution.

## Known limitations

- No live LLM, API client, platform connector, scraping, scheduling, posting or message sending.
- Discovery and retry modules replay supplied observations; they do not control a browser or reproduce the original private codebase.
- The event brief informs the prompt examples; Python loads the fixed draft fixtures and does not generate new copy from the brief.
- Exact ID / message deduplication can miss paraphrases and can merge identical questions from distinct people. A real CRM needs a consented stable contact identifier and event-level deduplication.
- Topic labels, permission, urgency and lifecycle state are manually supplied. The rubric is an unvalidated heuristic.
- The JSON ledger is single-user, has a fixed synthetic date, and is not safe for concurrent approvals. It records approval, not actual delivery or a complete CRM lifecycle.
- The report is read-only HTML; GitHub does not render it as a hosted app automatically.
- Manual prompt outputs must still be checked. No automated personal-information scanner or factual-verification system is claimed.

## Possible extensions

Only after validating the workflow: structured model outputs with explicit unknowns, a reviewed import step, contact-level deduplication, an actual audit log, a timezone-aware date, a proper database, and a controlled pilot with human quality ratings. These are planned options, not implemented features.
