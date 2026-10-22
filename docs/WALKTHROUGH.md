# Project walkthrough

**Purpose:** Provide a short demonstration and interview guide, with clear explanations of the outputs. Read this when you want to explore the project hands-on.

[Back to the project overview](../README.md) · [Next: evaluation and limitations](EVALUATION.md)

## What this project demonstrates

This project draws on practical Xiaohongshu content, post-discovery and interaction work, including iterative debugging. The public repository is a sanitized reconstruction: it separates the operating problem, implementation decisions and reproducible demonstrations from private account materials.

The executable prototype replays discovery, interaction verification and retry-state debugging, supported by content, inquiry triage and handoff. Start with the historical scale: 606 lead/context records, 1,771 events, 39 execution records across 29 distinct dates, and 95 mentor profiles in the saved snapshot. The public record-level examples are synthetic and match those table volumes; the aggregate counts are historical. Neither establishes revenue or measured efficiency gain.

Post discovery and interaction debugging are an important part of the broader project story. Read the repository's debugging documentation for the available historical evidence, the scope of the reconstruction and unresolved limitations. Do not infer a particular bug, diagnosis or successful fix from this walkthrough alone.

## A useful reading order

1. Start with the [README](../README.md) for the business context and current scope.
2. Read the [debugging case](DEBUGGING_CASE_STUDY.md) for the central problem and the [discovery rules](DISCOVERY_AND_INTERACTION.md) for the operating context.
3. Download the repository and open [the HTML report](../outputs/report.html) locally. GitHub shows its source rather than a live page. Inspect the [backend data model](BACKEND_DATA_MODEL.md) and [public CSVs](../data/synthetic_backend/) for scale and relationships.
4. For a technical review, read [discovery.py](../workflow/discovery.py) and [recovery.py](../workflow/recovery.py). Then inspect `deduplicate`, `prioritize` and `approve` in [pipeline.py](../workflow/pipeline.py) for the supporting inquiry example.
5. Run the tests and use [the evaluation guide](EVALUATION.md) to interpret the results. Expand the report's small regression-fixture section only when checking individual rules.

## Run and interpret the inquiry demonstration

Run `python -m workflow demo` from the repository root, then open `outputs/report.html` in a browser. The baseline reads 12 synthetic inquiry records and removes one exact duplicate. Of the 11 unique inquiries, five enter the eligible review queue. Six are held because of topic scope, follow-up permission or lifecycle state.

The priority score is a transparent operating rule, not a conversion probability. Inquiry triage means sorting records into review or hold, with a reason. The goal, timeline, permission and lifecycle fields are supplied in the input; the Python demonstration does not infer them from a live message.

Three fixed English content examples illustrate a two-day editorial planning cycle. Running the program does not ask an LLM to create new posts. The prompt pack documents a separate assisted drafting process, with factual checking and human review still required.

The fictional approval ledger starts with nine approvals on the fixed demonstration date. One additional approval can use the remaining daily review slot. Repeating that approval does not consume another slot. A different approval is then blocked. This demonstrates a local review allowance, not an official platform limit, a real sending count or a production delivery system.

### Optional: reproduce the approval boundary

Use a new ledger path for a clean experiment. These commands write only local example files:

```bash
python -m workflow approve --id SYN-001 --reviewer demo_operator --ledger runtime/walkthrough_ledger.json --out runtime/walkthrough_outputs
python -m workflow approve --id SYN-001 --reviewer demo_operator --ledger runtime/walkthrough_ledger.json --out runtime/walkthrough_outputs
python -m workflow approve --id SYN-002 --reviewer demo_operator --ledger runtime/walkthrough_ledger.json --out runtime/walkthrough_outputs
```

The first command records the remaining slot. The second does not count it twice. The third returns an expected limit error. The generated approval manifest records a review decision; it does not send anything.

## Explain the work in an interview

Discuss the business problem first: content research, relevant conversations, incoming inquiries and team handoffs can lose context when handled across disconnected steps. Then explain how you investigated behavior, checked outcomes and refined the process. Keep each debugging claim tied to a concrete record and state the limits of the evidence.

For the prototype, explain why draft preparation is separated from operational control. AI can assist with organizing material and preparing language; people retain responsibility for factual approval, the appropriateness of an interaction and the final next step.

A concise description is: "I translated an education-marketing workflow into a reproducible public prototype. The work connects post discovery and interaction debugging with content preparation, inquiry review and handoff. I distinguish historical observations from reconstructed tests, and I use synthetic data to make the operating decisions inspectable without exposing private materials."

## Keep claims proportional to evidence

The source code, synthetic fixtures and acceptance checks demonstrate specific behavior in this repository. They do not establish production autonomy, reliable live platform access, model accuracy, revenue attribution or measured time savings.

The implementation was developed with AI assistance. Understanding the main functions, the business rules and the debugging evidence is more useful than presenting a long tool list. Additional technical components should address a real operating need rather than decorate the portfolio.
