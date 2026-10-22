"""Offline, deterministic demonstration. No platform or model API calls."""

import argparse
import hashlib
import html
import json
import re
from pathlib import Path

from .discovery import plan_posts, verify_interaction
from .recovery import replay_debug_case
from .backend import analyze_backend

ROOT = Path(__file__).resolve().parents[1]
DEMO_DATE = "2026-01-12"
DAILY_REVIEW_CAP = 10
FIT_TOPICS = {"bioinformatics", "biomedical", "research_preparation"}
TERMINAL_STAGES = {"closed", "handed_off", "hold"}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_synthetic(rows):
    """Reject unlabeled rows: this demo intentionally accepts synthetic data only."""
    for row in rows:
        if row.get("synthetic") is not True:
            raise ValueError("Every input row must explicitly set synthetic=true.")


def deduplicate(rows):
    """Keep first occurrence of each record ID or normalized inquiry text."""
    unique, duplicates = [], []
    seen_ids, seen_messages = set(), set()
    for row in rows:
        identity = row["id"]
        normalized = re.sub(r"\s+", " ", row["message"].strip().casefold())
        if identity in seen_ids or normalized in seen_messages:
            duplicates.append({"id": identity, "reason": "duplicate_id_or_exact_message"})
            continue
        seen_ids.add(identity)
        seen_messages.add(normalized)
        unique.append(row)
    return unique, duplicates


def prioritize(row):
    """Transparent operating rubric; not ML or a conversion-probability estimate."""
    reasons, score = [], 0
    for condition, points, label in [
        (row.get("explicit_request") is True, 40, "explicit_request"),
        (row.get("topic") in FIT_TOPICS, 30, "topic_in_scope"),
        (bool(row.get("degree_goal")) and bool(row.get("timeline")), 20, "goal_and_timeline_provided"),
        (row.get("time_sensitive") is True, 10, "explicit_time_sensitive_request"),
    ]:
        if condition:
            score += points
            reasons.append({"rule": label, "points": points})
    missing = [field for field in ("degree_goal", "timeline") if not row.get(field)]
    blocked = []
    if row.get("topic") not in FIT_TOPICS:
        blocked.append("out_of_scope")
    if row.get("followup_permission") is not True:
        blocked.append("followup_not_requested")
    if row.get("stage") in TERMINAL_STAGES:
        blocked.append("inactive_or_already_handed_off")
    if blocked:
        next_step = "Hold for operator review; do not add an engagement action."
    elif missing:
        next_step = "Ask for missing information before a consultant handoff."
    else:
        next_step = "Review the inquiry and confirm the next step with the consultant."
    return {
        **row,
        "priority_score": score,
        "score_reasons": reasons,
        "missing_information": missing,
        "blocked_reasons": blocked,
        "next_step": next_step,
        "eligible_for_review": not blocked,
    }


def reply_draft(row):
    """Conservative template, not a live AI response or personalized advice."""
    if row["missing_information"]:
        return "Thanks for sharing your interests. Could you clarify your target degree and application timeline? A colleague can then review whether an appropriate next step is available."
    return "Thanks for outlining your background and question. A colleague can review the research direction and timing before confirming a next step; no mentor match, availability or admissions result is promised."


def load_ledger(path):
    path = Path(path)
    if path.exists():
        return read_json(path)
    return read_json(ROOT / "data" / "synthetic_review_ledger.json")


def approved_engagement_count(ledger, date):
    return sum(1 for entry in ledger if entry["date"] == date and entry["kind"] == "engagement" and entry["status"] == "approved")


def approval_status(identity, ledger, date):
    return "approved" if any(entry["id"] == identity and entry["status"] == "approved" for entry in ledger) else "pending_review"


def approve(identity, reviewer, ledger, queue, date):
    """Reserve a daily review slot after explicit operator action. Never sends."""
    if not reviewer.strip():
        raise ValueError("An explicit reviewer label is required.")
    item = next((item for item in queue if item["id"] == identity), None)
    if item is None:
        raise ValueError("This item is not in the eligible review queue.")
    if approval_status(identity, ledger, date) == "approved":
        return ledger  # Idempotent: repeated approval does not spend another slot.
    if approved_engagement_count(ledger, date) >= DAILY_REVIEW_CAP:
        raise ValueError("The daily engagement review allowance is exhausted.")
    return ledger + [{"id": identity, "date": date, "kind": "engagement", "status": "approved", "reviewer": reviewer, "synthetic": True}]


def build_outputs(rows, drafts, ledger, date=DEMO_DATE, posts=None, snapshot_profile=None, backend_analysis=None):
    validate_synthetic(rows)
    validate_synthetic(drafts)
    validate_synthetic(ledger)
    unique, duplicates = deduplicate(rows)
    leads = sorted((prioritize(row) for row in unique), key=lambda row: (-row["priority_score"], row["id"]))
    for row in leads:
        row["review_status"] = approval_status(row["id"], ledger, date) if row["eligible_for_review"] else "held"
    queue = [{
        "id": row["id"], "kind": "engagement", "priority_score": row["priority_score"],
        "status": approval_status(row["id"], ledger, date),
        "draft": reply_draft(row), "draft_method": "deterministic_template",
        "next_step": row["next_step"], "synthetic": True,
    } for row in leads if row["eligible_for_review"]]
    allowed = max(0, DAILY_REVIEW_CAP - approved_engagement_count(ledger, date))
    actions = [row for row in queue if row["status"] == "approved"]
    posts = posts or []
    discovery = plan_posts(posts)
    debug = replay_debug_case()
    verification = []
    if posts:
        base = {"synthetic": True, "observed_post_id": posts[0]["id"], "observed_author_id": posts[0]["author_id"]}
        cases = [
            ("complete visible comment and separately visible like", {**base, "comment_attempted": True, "complete_own_approved_comment_visible": True, "like_attempted": True, "liked_state_visible": True}),
            ("send click without visible result", {**base, "send_clicked": True, "input_cleared": True}),
            ("result displayed under a different post", {**base, "observed_post_id": "SYN-WRONG-POST", "comment_attempted": True, "complete_own_approved_comment_visible": True}),
        ]
        verification = [{"scenario": label, **verify_interaction(posts[0], observation)} for label, observation in cases]
    metrics = {
        "synthetic": True, "demo_date": date,
        "metric_scope": "small_regression_fixtures_only; historical and full-volume backend counts are separate outputs",
        "input_records": len(rows), "unique_inquiries": len(unique),
        "duplicates_removed": len(duplicates),
        "eligible_review_items": len(queue), "blocked_inquiries": len(unique) - len(queue),
        "content_drafts": len(drafts),
        "approved_engagements_today_including_seed": approved_engagement_count(ledger, date),
        "remaining_review_allowance": allowed, "approved_current_items": len(actions),
        "platform_messages_sent": 0, "platform_posts_published": 0,
        "post_candidates": len(discovery),
        "posts_eligible_for_review": sum(item["eligible_for_review"] for item in discovery),
        "recovery_states_replayed": len(debug["steps"]),
        "note": "Synthetic workflow counts, not campaign performance, conversion rates, or AI accuracy.",
    }
    return {"backend_snapshot_profile": snapshot_profile or {}, "synthetic_backend_analysis": backend_analysis or {},
            "discovery_plan": discovery, "interaction_verification": verification, "debug_replay": debug,
            "leads": leads, "duplicates": duplicates, "review_queue": queue, "content_drafts": drafts, "action_manifest": actions, "metrics": metrics}


def render_report(result):
    """Create a self-contained, recruiter-readable view of the public case study."""
    esc = html.escape
    readable = lambda value: esc(str(value).replace("_", " "))
    yes_no = lambda value: "Yes" if value else "No"
    metrics = result["metrics"]
    profile = result.get("backend_snapshot_profile", {})
    tiles = "".join(f'<div class="tile"><b>{row["records"]:,}</b><span>{esc(row["meaning"])}</span></div>' for row in profile.get("tables", []))
    scale_rows = "".join(f'<tr><th scope="row">{esc(row["meaning"])}</th><td>{row["records"]:,}</td><td>{row["source_columns"]}</td><td>{"CSV and Excel counts agree" if row["workbook_checked"] else "CSV profile count"}</td></tr>' for row in profile.get("tables", []))
    stage_rows = "".join(f'<tr><th scope="row">{readable(row["label"])}</th><td>{row["records"]:,}</td></tr>' for row in profile.get("lead_stage_distribution", []))
    backend = result.get("synthetic_backend_analysis", {})
    public_rows = "".join(f'<tr><th scope="row">{readable(name)}</th><td>{count:,}</td></tr>' for name, count in backend.get("row_counts", {}).items())
    relationships = backend.get("relationships", {})
    relationship_rows = "".join(f'<tr><th scope="row">{esc(label)}</th><td>{relationships[key]:,}</td></tr>' for key, label in [
        ("events_with_valid_lead", "Synthetic events referencing an existing lead"),
        ("events_with_valid_run", "Synthetic events referencing an existing run"),
        ("distinct_leads_with_events", "Synthetic leads with event history"),
        ("unknown_mentor_references", "Unknown synthetic mentor references"),
    ] if key in relationships)
    discovery_rows = "".join(f'<tr><th scope="row">{esc(row["post_id"])}</th><td>{esc(row["anchor"] or "Unknown")}</td><td>{readable(row["status"])}</td><td>{readable(", ".join(row["reasons"]))}</td></tr>' for row in result["discovery_plan"])
    verification_rows = "".join(f'<tr><th scope="row">{esc(row["scenario"]).capitalize()}</th><td>{readable(row["comment_status"])}</td><td>{readable(row["like_status"])}</td><td>{yes_no(row["pair_verified"])}</td></tr>' for row in result["interaction_verification"])
    debug_rows = "".join(f'<tr><th scope="row">{esc(row["label"])}</th><td>{readable(row["phase"])}</td><td>{yes_no(row["retry_budget_reserved"])}</td><td>{readable(row["error_class"] or "None")}</td><td>{yes_no(row["stopped"])}</td></tr>' for row in result["debug_replay"]["steps"])
    lead_rows = "".join(f'<tr><th scope="row">{esc(row["id"])}</th><td>{readable(row["topic"])}</td><td>{row["priority_score"]}</td><td>{readable(", ".join(row["blocked_reasons"]) or row["review_status"])}</td><td>{esc(row["next_step"])}</td></tr>' for row in result["leads"])
    cards = "".join(f'<article><small>{esc(row["id"])} · SYNTHETIC DRAFT · PENDING REVIEW</small><h4>{esc(row["title"])}</h4><p>{esc(row["body"])}</p><p class="muted">{esc(row["review_note"])}</p></article>' for row in result["content_drafts"])
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Yi Liang's public case study in XHS workflow debugging, interaction verification, and marketing operations.">
<title>XHS Discovery, Interaction &amp; AI Operations | Yi Liang</title>
<style>
*{{box-sizing:border-box}}html{{scroll-padding-top:24px}}body{{margin:0;background:#f3f5f7;color:#17202b;font:16px/1.65 system-ui,sans-serif}}main{{max-width:1120px;margin:auto;padding:36px 24px 48px}}header{{background:#112d38;color:#fff;padding:36px;border-radius:18px}}h1{{font-size:clamp(28px,4vw,44px);line-height:1.15;max-width:820px;margin:12px 0 18px}}h2{{font-size:26px;line-height:1.25;margin:0 0 16px}}h3{{font-size:19px;line-height:1.35;margin:0 0 10px}}h4{{font-size:17px;line-height:1.4;margin:12px 0}}p{{margin:0 0 16px;max-width:80ch}}p:last-child{{margin-bottom:0}}a{{color:#0a5268;text-underline-offset:3px}}a:focus-visible,summary:focus-visible,.scroll:focus-visible{{outline:3px solid #b85c12;outline-offset:4px}}.skip{{position:absolute;left:-9999px}}.skip:focus{{left:16px;top:12px;background:#fff;padding:10px;z-index:5}}.eyebrow,small{{font-size:12px;letter-spacing:.06em}}.eyebrow{{font-weight:700}}.tag{{display:inline-block;background:#dff3dc;color:#183827;padding:5px 12px;border-radius:24px;font-size:12px;font-weight:700;margin-top:4px}}nav{{display:flex;flex-wrap:wrap;gap:10px 24px;padding:20px 0;font-size:14px;font-weight:600}}.tiles{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:16px 0}}.tile,article{{background:#fff;padding:24px;border:1px solid #dce3e7;border-radius:12px}}.tile b{{display:block;font-size:34px;line-height:1.25;margin-bottom:8px}}.tile span,.muted,.note{{color:#52616c;font-size:14px}}section{{margin-top:40px}}.section-label{{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:#456372;font-weight:700;margin-bottom:8px}}.three{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:20px 0}}.three article p{{font-size:15px}}.callout{{background:#e4eef1;border-left:4px solid #1a647a;padding:18px 22px;margin:20px 0;border-radius:0 8px 8px 0}}.scroll{{overflow-x:auto;margin:16px 0;border:1px solid #dce3e7;border-radius:10px;background:#fff}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{padding:13px 16px;text-align:left;border-bottom:1px solid #dce3e7;vertical-align:top;overflow-wrap:anywhere}}thead th{{background:#e4ecef;color:#263f4c;font-weight:700}}tbody th{{font-weight:500}}tr:last-child td,tr:last-child th{{border-bottom:0}}caption{{text-align:left;padding:14px 16px;font-size:14px;font-weight:700;color:#365262;background:#f8fafb}}details{{border:1px solid #dce3e7;background:#fff;border-radius:12px;padding:18px 22px;margin:20px 0}}summary{{cursor:pointer;font-weight:650;line-height:1.5}}details[open] summary{{margin-bottom:18px}}details h3{{margin-top:24px}}code{{font:13px/1.6 ui-monospace,monospace;background:#e7edf0;padding:2px 5px;border-radius:4px;overflow-wrap:anywhere}}.drafts{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}article p{{white-space:pre-line}}footer{{margin-top:40px;border-top:1px solid #ccd9df;padding-top:22px;color:#52616c;font-size:14px}}ul{{padding-left:22px;margin:12px 0 0}}li{{margin-bottom:9px}}@media(max-width:750px){{main{{padding:20px 16px 36px}}header{{padding:24px}}.tiles{{grid-template-columns:repeat(2,minmax(0,1fr))}}.three,.drafts{{grid-template-columns:1fr}}h2{{font-size:23px}}section{{margin-top:32px}}.tile{{padding:18px}}th,td{{padding:11px 12px}}details{{padding:16px}}.scroll table{{min-width:530px}}}}@media print{{body{{background:#fff}}main{{max-width:none;padding:0}}header{{background:#fff;color:#17202b;border:1px solid #dce3e7}}nav,.skip{{display:none}}section,article,.tile{{break-inside:avoid}}}}
</style>
</head>
<body>
<a class="skip" href="#overview">Skip to project overview</a>
<main>
<header>
<div class="eyebrow">YI LIANG / WORKFLOW DEBUGGING &amp; MARKETING OPERATIONS</div>
<h1>XHS Discovery, Interaction &amp; AI Operations</h1>
<p>A public case study in making social outreach easier to review, verify and hand off. Built from my work with an independent PhD application advisory studio on Xiaohongshu (XHS), a social content platform.</p>
<span class="tag">HISTORICAL AGGREGATE COUNTS · SYNTHETIC PUBLIC RECORDS</span>
</header>
<nav aria-label="Report sections"><a href="#overview">Overview</a><a href="#debugging">Debugging case</a><a href="#discovery">Discovery &amp; verification</a><a href="#data">Data model</a><a href="#supporting">Supporting workflow</a></nav>
<section id="overview">
<div class="section-label">Project at a glance</div>
<h2>From a relevant post to a reliable next step</h2>
<p>My contribution was to refine discovery and interaction rules, investigate uncertain action results, define recovery behavior, and preserve context for a colleague's follow-up. I built this separate public prototype with AI-assisted coding and documentation.</p>
<div class="tiles">{tiles}</div>
<p class="note">Historical saved-record counts across {profile.get("distinct_run_dates", "unknown")} distinct recorded run dates. These are records, not paying customers, successful contacts or currently available mentors. All public row-level data is synthetic.</p>
<div class="three">
<article><h3>Operational judgment</h3><p>Evaluate the original request, relevance and prior contact history before preparing a contextual interaction.</p></article>
<article><h3>Debugging and verification</h3><p>Separate an intended action, a submitted attempt and a verified result. Preserve uncertainty when evidence is missing.</p></article>
<article><h3>Structured marketing data</h3><p>Connect leads, events, execution runs and resource profiles so review decisions and handoffs stay inspectable.</p></article>
</div>
</section>
<section id="debugging">
<div class="section-label">Core case study</div>
<h2>Debugging an action with an unknown result</h2>
<div class="three">
<article><h3>1. Diagnose the ambiguity</h3><p>A retry allowance was reserved, but a combined recovery-and-observation request did not establish whether the action executed. A later healthy page could not resolve that missing evidence.</p></article>
<article><h3>2. Separate the states</h3><p>The isolated correction distinguished reservation, submitted attempt, acknowledged success, acknowledged failure and unknown outcome. Observations stayed separate from action results.</p></article>
<article><h3>3. Verify the boundary</h3><p>Archived diagnostic records reported 20 passing synthetic checks on an isolated copy. The external access restriction remained unresolved; the original trial stayed stopped.</p></article>
</div>
<div class="callout"><strong>Key decision:</strong> an uncertain action is not automatically repeated. Keep the used allowance, stop condition and completed history until the result can be established.</div>
<p class="note">The replay below is a fresh public reconstruction with fictional records. Its tests are separate from the 20 archived checks; the counts should not be combined. It makes no live browser call.</p>
<details><summary>Inspect the recovery-state replay</summary>
<p>A recorded success does not by itself restart the workflow. The stop flag, completed history and deadline are preserved independently.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Recovery replay table"><table><caption>Synthetic recovery-state sequence</caption><thead><tr><th scope="col">Observation or action</th><th scope="col">Recorded state</th><th scope="col">Allowance reserved</th><th scope="col">Error classification</th><th scope="col">Stopped</th></tr></thead><tbody>{debug_rows}</tbody></table></div>
</details>
</section>
<section id="discovery">
<div class="section-label">Core operating method</div>
<h2>Find relevant context, then verify the result</h2>
<p>Discovery means reviewing a post encountered in the visible feed, rather than running a search crawler. Review the original post, author context, stated need and cross-run history; sparse profile information alone does not invalidate a coherent request.</p>
<p>Verify the complete intended comment under the correct post and account, then check the liked state separately. A send click, cleared text box or changed counter is insufficient.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Interaction verification examples"><table><caption>Small synthetic examples: verify the result, not the click</caption><thead><tr><th scope="col">Scenario</th><th scope="col">Comment result</th><th scope="col">Like result</th><th scope="col">Both verified</th></tr></thead><tbody>{verification_rows}</tbody></table></div>
<details><summary>Inspect the nine-post discovery test set</summary>
<p>These small test examples, also called regression fixtures, isolate individual rules. They are not the size of the historical backend. No browser navigation or contact occurs.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Discovery decisions"><table><caption>Synthetic visible-feed candidates</caption><thead><tr><th scope="col">Post ID</th><th scope="col">Relevant context</th><th scope="col">Decision</th><th scope="col">Reason</th></tr></thead><tbody>{discovery_rows}</tbody></table></div>
</details>
</section>
<section id="data">
<div class="section-label">Scale and data structure</div>
<h2>A backend that preserves the operating history</h2>
<p>Lead records retain the latest context; event records retain individual operations; run records summarize execution; mentor profiles support direction matching. The public CSVs preserve the historical table volumes with entirely new records and relationships.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Public synthetic table volumes"><table><caption>Public full-volume data model: every bundled row is loaded</caption><thead><tr><th scope="col">Synthetic table</th><th scope="col">Rows loaded</th></tr></thead><tbody>{public_rows}</tbody></table></div>
<details><summary>Inspect historical counts and synthetic relationship checks</summary>
<h3>Backend scale from the historical snapshot</h3>
<p>Period: {esc(profile.get("snapshot_period", "Not supplied"))}. Lead, event and run counts were reconciled between saved CSV files and Excel views. The mentor total comes from the CSV snapshot.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Historical record reconciliation"><table><caption>Historical aggregate profile</caption><thead><tr><th scope="col">Record type</th><th scope="col">Actual records</th><th scope="col">Source columns</th><th scope="col">Reconciliation</th></tr></thead><tbody>{scale_rows}</tbody></table></div>
<h3>Recorded lead states</h3><p>Top stored labels, with other states grouped together. This is the saved state distribution, not a conversion funnel.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Historical lead state distribution"><table><caption>Historical state summary</caption><thead><tr><th scope="col">Stored state</th><th scope="col">Records</th></tr></thead><tbody>{stage_rows}</tbody></table></div>
<h3>Synthetic relationship checks</h3><p>These checks apply to the new public data, not private source rows.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Synthetic data relationship checks"><table><caption>Checks on the bundled synthetic tables</caption><thead><tr><th scope="col">Check</th><th scope="col">Records</th></tr></thead><tbody>{relationship_rows}</tbody></table></div>
</details>
</section>
<section id="supporting">
<div class="section-label">Supporting demonstration</div>
<h2>Prepare content and a clear consultant handoff</h2>
<p>The supporting example removes duplicate inquiries, explains a simple priority score, records missing information and produces a review queue. Drafts remain pending review; a score is an operating rule, not a conversion probability or admissions assessment.</p>
<p class="note">This small test set contains {metrics["input_records"]} inquiry records, {metrics["duplicates_removed"]} exact duplicate, {metrics["eligible_review_items"]} eligible review items and {metrics["blocked_inquiries"]} held items. It is separate from the full-volume tables above.</p>
<details><summary>Inspect the inquiry queue and three content examples</summary>
<div class="scroll" tabindex="0" role="region" aria-label="Synthetic inquiry triage"><table><caption>Supporting inquiry triage fixture</caption><thead><tr><th scope="col">Inquiry ID</th><th scope="col">Topic</th><th scope="col">Score / 100</th><th scope="col">Review state or hold reason</th><th scope="col">Next step</th></tr></thead><tbody>{lead_rows}</tbody></table></div>
<h3>Three draft concepts for a planning cycle</h3><p>Fixed English adaptations illustrate an assisted editorial workflow. They are not live LLM output or original account content.</p>
<div class="drafts">{cards}</div>
</details>
</section>
<footer><strong>Scope and privacy.</strong> Historical aggregate counts are identified separately from synthetic records. Exact operating dates, organizational identity, social accounts and private mentor information are withheld. This offline prototype does not browse, post, message or call a model API. No revenue or measured efficiency gain is claimed.</footer>
</main>
</body>
</html>'''


def export_outputs(result, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for key, value in result.items():
        write_json(out / f"{key}.json", value)
    (out / "report.html").write_text(render_report(result) + "\n", encoding="utf-8")
    scores = "\n".join(f'| {row["id"]} | {row["priority_score"]} | {", ".join(reason["rule"] for reason in row["score_reasons"])} | {", ".join(row["blocked_reasons"]) or row["review_status"]} |' for row in result["leads"])
    (out / "triage.md").write_text("# Synthetic inquiry triage\n\nAll records are fictional. Scores are operational rules, not probabilities.\n\n| ID | Score | Reasons | Review state / blocks |\n|---|---:|---|---|\n" + scores + "\n", encoding="utf-8")
    fingerprint = hashlib.sha256((json.dumps(result, sort_keys=True, ensure_ascii=False) + "\n").encode()).hexdigest()
    (out / "reproducibility.txt").write_text(f"Result SHA-256: {fingerprint}\nFixed synthetic date: {DEMO_DATE}\nNetwork calls: 0\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["demo", "approve"], nargs="?", default="demo")
    parser.add_argument("--id", help="Eligible synthetic inquiry ID to approve")
    parser.add_argument("--reviewer", default="", help="Explicit operator label")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs")
    parser.add_argument("--ledger", type=Path, default=ROOT / "runtime" / "review_ledger.json")
    args = parser.parse_args()
    rows = read_json(ROOT / "data" / "synthetic_inquiries.json")
    drafts = read_json(ROOT / "data" / "synthetic_content_drafts.json")
    posts = read_json(ROOT / "data" / "synthetic_posts.json")
    snapshot = read_json(ROOT / "data" / "backend_snapshot_profile.json")
    backend = analyze_backend()
    ledger = load_ledger(args.ledger)
    result = build_outputs(rows, drafts, ledger, posts=posts, snapshot_profile=snapshot, backend_analysis=backend)
    if args.command == "approve":
        if not args.id:
            parser.error("approve requires --id and --reviewer")
        try:
            ledger = approve(args.id, args.reviewer, ledger, result["review_queue"], DEMO_DATE)
        except ValueError as exc:
            parser.error(str(exc))
        write_json(args.ledger, ledger)
        result = build_outputs(rows, drafts, ledger, posts=posts, snapshot_profile=snapshot, backend_analysis=backend)
    export_outputs(result, args.out)
    print(json.dumps({
        "historical_snapshot_period": snapshot["snapshot_period"],
        "historical_record_counts": {row["name"]: row["records"] for row in snapshot["tables"]},
        "public_synthetic_rows_loaded": backend["row_counts"],
        "distinct_recorded_run_dates": snapshot["distinct_run_dates"],
        "regression_fixtures": result["metrics"],
    }, ensure_ascii=False, indent=2))
    print(f"Report: {args.out / 'report.html'}")


if __name__ == "__main__":
    main()
