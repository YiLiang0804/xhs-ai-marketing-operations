# Case study: connecting discovery, reliable interaction and the next step

**Purpose:** Explain the business problem, my contribution and the decisions behind the public prototype. Start here for the marketing-operations story.

[Back to the project overview](../README.md) · [Next: the debugging case](DEBUGGING_CASE_STUDY.md)

## Context

My education-marketing work has involved relevant-post discovery, contextual interaction, social content, event promotion, inbound questions and team handoffs. A useful workflow must connect those activities without turning uncertain observations into confident execution claims.

This repository reconstructs that operating problem with a separate historical aggregate profile and synthetic public records. The saved backend contains 606 lead/context records, 1,771 event records, 39 execution records and 95 mentor profiles. Private source rows, account history and identities are not released. The Python application was created for this portfolio; it is not a claim that this exact implementation was deployed at work.

## Objective

Create an inspectable path from a discovered post to a verified interaction and a clear handoff, supported by content and inquiry operations. Debugging uncertainty about whether an action actually ran is central: see [the debugging case](DEBUGGING_CASE_STUDY.md). The intended users are a marketing operator and a consulting colleague.

## Decisions and trade-offs

### 1. Separate generation from operational control

A large language model (LLM) can help organize a brief, explore copy directions, or summarize a question. It should not quietly invent event dates, speaker credentials, availability or outcomes. The [prompt pack](../prompts/) requires explicit unknowns and a pending-review status.

The executable demo uses fixed content examples and deterministic reply templates. This keeps it runnable without a model account and makes the review rules easy to verify. Live LLM generation is a potential extension, not a current feature.

### 2. Use a simple, visible inquiry rubric

The prototype ranks inquiries using stated request, topic fit, completeness and explicit time sensitivity. It does not infer sensitive traits, financial capacity or admissions prospects. Permission and lifecycle checks are separate from the numeric score: a high score cannot override a closed or already handed-off record.

### 3. Preserve the consultant's role

A marketing operator should not promise a particular mentor, service fit or outcome. The next step is either clarification, hold, or a consultant review. The review queue retains missing fields and the next-step rationale rather than presenting a model judgment as a final decision.

### 4. Preserve historical authorization distinctions

The historical specification separated eligible public interactions under scoped standing authorization from individually approved private messages. It also distinguished proactive messages from inbound replies. The public replay does not import those permissions or execute contact. It reconstructs decision and verification logic with synthetic records.

### 5. Bound the supporting review example

The synthetic review ledger demonstrates a ten-item daily engagement-review allowance. Repeating an approval does not consume another slot; this is called **idempotent approval**. The stored ledger is a local, single-user JSON file; it cannot safely coordinate simultaneous reviewers. The fixed demonstration date makes the example reproducible. No scheduling or actual platform action is implemented.

### 6. Make failure cases part of the story

The examples include sparse-profile context, repeated authors, an unverified target, an uncertain send, a duplicate inquiry, unrelated requests, missing information and a completed handoff. The retry reconstruction preserves the distinction between reserved budget and acknowledged execution. Synthetic regression cases are labeled separately from historically observed incidents.

## My contribution

- Translate the business problem into inputs, stages, review decisions and handoff requirements.
- Define a transparent prioritization rubric and a distinction between relevance and permission to follow up.
- Structure English public adaptations of content concepts for a biology-focused audience, with a focused topic and restrained call to action (CTA).
- Translate the documented discovery, verification and retry-state issues into isolated public regression tests.
- Build and document the public prototype with AI assistance, then verify its operational boundaries.
- Specify a pilot evaluation that separates process quality from downstream business outcomes.

## Evidence in this release

The release includes runnable source, small regression fixtures, matching-volume synthetic backend tables, real aggregate counts, reproducible outputs and acceptance checks. The historical case study is based on archived operating and diagnostic records; private originals are not distributed. Its 20 reported isolated tests are distinct from the current public suite. No measured before/after business experiment is included.

## What I would validate next

With approved materials and an authorized pilot, I would first test whether a colleague can review and hand off an inquiry correctly using the output alone. Then I would measure reviewer effort, revisions, missed follow-ups and unsupported factual claims. A model integration would be useful only if its drafts improve that process at acceptable cost and review effort.
