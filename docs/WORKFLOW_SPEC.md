# Supporting content and inquiry specification

**Purpose:** Define the inputs, review rules and handoff steps for the supporting content and inquiry example. Read this for operational detail after the core discovery and debugging story.

[Back to the project overview](../README.md) · [Next: evaluation and limitations](EVALUATION.md)

This is a new public specification abstracted from an education-marketing use case. It uses fictional inputs and does not reproduce private account material. Some stages are documented operating steps; only the offline components described in the README run in Python.

The primary discovery, interaction and debugging portions are described in [the discovery rules](DISCOVERY_AND_INTERACTION.md) and [the debugging case](DEBUGGING_CASE_STUDY.md). This file covers the supporting content/inquiry example. Its ten-item review allowance is a new portfolio fixture, not the original contact policy.

## 1. Prepare an authorized brief

The operator records audience, one focused topic, campaign objective, known facts, unknowns and the intended next step. Any reference posts must be provided through an authorized source. This repository does not retrieve posts, analytics or colleagues' accounts.

For a Bio audience, start with the research question or preparation concern rather than a list of prestigious institutions. A cover concept can use a restrained dark, text-led style. That preference is an editorial choice, not a validated performance result in this project.

## 2. Prepare three draft concepts

Use [the content-drafting prompt](../prompts/01_content_drafting.md) with the brief. Each concept includes an audience, title, hook, body, call to action (CTA), tags and a list of facts to verify. Keep topics distinct within a two-day planning cycle. Unknown speaker and event details remain unknown.

The public demo contains three fixed examples. It does not schedule their generation or publication. A real operator edits drafts and chooses whether and when to publish them.

## 3. Structure inbound inquiries

In an authorized private workflow, record only the information necessary for the next step. The public example replaces people and conversations with synthetic record IDs and fictional messages.

| Field | Meaning | If unknown |
|---|---|---|
| `id` | Synthetic inquiry identity for this demonstration | Reject invalid input rather than invent a contact |
| `message` | Fictional inbound question | Do not infer a request from silence |
| `topic` | Operator-assigned subject label | Review manually before routing |
| `degree_goal` | Explicitly stated goal | Keep null and request clarification |
| `timeline` | Explicitly stated planning window | Keep null and request clarification |
| `explicit_request` | Whether a request is clearly stated | Do not award the request points |
| `time_sensitive` | Whether urgency was explicitly stated | Do not infer urgency |
| `followup_permission` | Operator-supplied follow-up request / permission flag | No engagement approval |
| `stage` | Current inquiry lifecycle state | Must be reviewed before real use |
| `synthetic` | Required public-fixture marker | The demo rejects the row |

Labels and permission flags are supplied by a person in this prototype, not extracted by AI. Exact text deduplication is a demonstration shortcut; a real system needs contact-aware handling.

## 4. Review and choose a next step

The rules assign a visible priority score. In-scope active inquiries with follow-up requested can enter `pending_review`; out-of-scope, paused, closed and already handed-off items are held. The operator reviews the context, missing fields and draft reply.

[The optional inquiry-summary prompt](../prompts/02_inquiry_summary.md) can assist this review in a separate manual session. Its output is not automatically trusted or imported. A model cannot approve communication or silently infer consent.

The approval command demonstrates a ten-item daily engagement-review workload allowance. It records explicit approval in a local ledger. No platform action follows. The approval manifest can be inspected repeatedly and must not be treated as an executable sending queue.

## 5. Handoff and learn

Before a real consultant handoff, the operator checks: what the person asked, what is known, what remains missing, whether follow-up is wanted, and who owns the next step. A consultant confirms service scope and availability. Once handed off, the marketing inquiry should not re-enter a proactive follow-up queue without a deliberate lifecycle update.

The prototype reads the lifecycle state supplied in the fixture; it does not implement a production customer relationship management (CRM) update or handoff integration. Its metrics measure demonstration counts. For a real pilot, use [the evaluation definitions](EVALUATION.md) and log reviewer corrections before claiming any improvement.
