# Post discovery and contextual interaction

**Purpose:** Explain how a feed candidate becomes a context-aware interaction, with checks to prevent repeated or unverified contact. Read this for the operating rules behind the debugging case.

[Back to the project overview](../README.md) · [Next: backend data model](BACKEND_DATA_MODEL.md)

## Discovery method

The actual workflow was iteratively refined around naturally encountered visible-feed posts. Here, **discovery means evaluating a feed candidate**, not running a keyword-search crawler. Visible browser actions preserved the feed while a candidate post and its author's profile were read.

The public code replays that decision process with fictional records. It does not browse XHS, retrieve messages, open saved links, collect profiles or send interactions. Platform mechanics, private configuration and original source code are omitted.

## Candidate review

Check the current request, service fit, post/profile context, recency and interaction history. Distinguish an actual application need from an offer celebration, generic result comparison or unrelated content. A long post does not establish relevance or buying intent.

A sparse profile is not, by itself, a reason to reject a coherent and detailed request. This documented rule refinement prevents a profile-history threshold from overriding useful evidence in the original post. It is not proof of a measured conversion improvement.

Private service catalogs, exact business thresholds and contact identities are not distributed. Constants in the public fixtures are illustrative choices, not a live configuration.

## Context and identity

Retain the source post, author, intended recipient, reason for relevance and one concise context anchor. A liker can be different from the author; do not copy the author's background or goals to that person. Use post and author history across runs to avoid repeated contact.

Public fixtures use synthetic IDs only. They contain no real URLs, usernames, profile images, grades, conversations or mentor combinations.

## Draft and authorization

Prepare a short response anchored in the current request. Avoid generic copy rotation, unnecessary disclosure of internal resources and admissions promises. [The discovery-review prompt](../prompts/04_discovery_review.md) gives a new public reasoning template.

The historical specification distinguished eligible public comments under scoped standing authorization from private messages requiring individual approval. Inbound replies and proactive messages were handled separately. The reconstruction only records decisions: it neither imports prior approvals nor grants authorization.

## Verification

| Stage | Evidence needed |
|---|---|
| Before interaction | Intended post/person, context, current authorization, history check and a place to save progress |
| After comment attempt | Complete intended comment visibly present under the intended post from the intended account |
| After like attempt | Intended post's liked state separately visible |
| Before completion | Verified outcomes and progress records saved persistently |
| Unknown result | Preserve the attempt and stop; do not repeat the uncertain send |

A cleared input, changed counter or send click is supporting information, not proof of completion. Keep candidate context until verification and checkpointing (saving progress) are finished.

## Restart and migration

History and the latest checkpoint must remain consistent. A local browser tab identity is not reusable in another environment. A migration snapshot is not a shared database: a single authoritative writer and event-level merge avoid independent stale copies contacting the same person.

These are operating requirements, not a claim that the public Python replay implements distributed synchronization, browser migration or a production customer relationship management (CRM) system. The concrete historical retry-state issue is documented in [the debugging case](DEBUGGING_CASE_STUDY.md).
