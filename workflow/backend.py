"""Generate and analyze a volume-matched, fully synthetic public backend.

Only table record counts and the number of distinct run dates match the
reviewed historical snapshot. Every value, date, relationship, distribution,
identifier and outcome is newly constructed. No private source is read here.
"""

import csv
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "data" / "synthetic_backend"
REFERENCE_COUNTS = {"leads": 606, "events": 1771, "runs": 39, "mentors": 95}
REFERENCE_DISTINCT_RUN_DATES = 29
SCHEMAS = {
    "leads": ["lead_id", "topic", "stage", "mentor_id", "synthetic"],
    "events": ["event_id", "run_id", "lead_id", "event_type", "event_status", "synthetic"],
    "runs": ["run_id", "run_date", "status", "synthetic"],
    "mentors": ["mentor_id", "specialty", "availability", "synthetic"],
}
KEYS = {"leads": "lead_id", "events": "event_id", "runs": "run_id", "mentors": "mentor_id"}


def build_synthetic_backend():
    """Construct fictional relational tables; historical rows are never copied."""
    topics = ["Research preparation", "Bioinformatics", "Biomedical research", "Application planning", "Research statement"]
    specialties = ["Biology", "Computer science", "Engineering", "Public health", "Business"]
    runs = [{
        "run_id": f"SYN-RUN-{i + 1:03d}",
        "run_date": (date(2030, 1, 1) + timedelta(days=i % REFERENCE_DISTINCT_RUN_DATES)).isoformat(),
        "status": ["completed", "paused", "review_pending"][i % 3],
        "synthetic": True,
    } for i in range(REFERENCE_COUNTS["runs"])]
    mentors = [{
        "mentor_id": f"SYN-MENTOR-{i + 1:03d}",
        "specialty": specialties[i % len(specialties)],
        "availability": ["available_for_demo", "paused_for_demo", "needs_demo_confirmation"][i % 3],
        "synthetic": True,
    } for i in range(REFERENCE_COUNTS["mentors"])]
    leads = [{
        "lead_id": f"SYN-LEAD-{i + 1:04d}",
        "topic": topics[i % len(topics)],
        "stage": ["candidate", "context_review", "draft_pending", "awaiting_reply", "handoff_review", "held"][i % 6],
        "mentor_id": "" if i % 4 == 0 else mentors[i % len(mentors)]["mentor_id"],
        "synthetic": True,
    } for i in range(REFERENCE_COUNTS["leads"])]
    # These invented allocations illustrate several event kinds. They are not
    # the historical event distribution and must not be reported as results.
    allocations = [
        (606, "candidate_discovered", "recorded"),
        (250, "context_reviewed", "recorded"),
        (150, "draft_prepared", "pending_review"),
        (100, "comment_attempted", "attempt_recorded"),
        (90, "comment_verified", "observed"),
        (90, "like_attempted", "attempt_recorded"),
        (85, "like_verified", "observed"),
        (50, "inbound_received", "recorded"),
        (40, "reply_draft_prepared", "pending_review"),
        (25, "reply_approved", "approved"),
        (25, "reply_attempted", "attempt_recorded"),
        (20, "reply_verified", "observed"),
        (240, "checkpoint_recorded", "recorded"),
    ]
    events = []
    for count, kind, status in allocations:
        for lead_index in range(count):
            events.append({
                "event_id": f"SYN-EVENT-{len(events) + 1:05d}",
                "run_id": runs[lead_index % len(runs)]["run_id"],
                "lead_id": leads[lead_index]["lead_id"],
                "event_type": kind, "event_status": status, "synthetic": True,
            })
    return {"leads": leads, "events": events, "runs": runs, "mentors": mentors}


def validate_backend(tables):
    """Validate the public demonstration's counts, labels and relationships."""
    for table, expected in REFERENCE_COUNTS.items():
        rows = tables[table]
        if len(rows) != expected:
            raise ValueError(f"Unexpected {table} row count.")
        if any(row.get("synthetic") is not True for row in rows):
            raise ValueError(f"Every {table} row must explicitly be synthetic.")
        if any(set(row) != set(SCHEMAS[table]) for row in rows):
            raise ValueError(f"Unexpected {table} public schema.")
        values = [row[KEYS[table]] for row in rows]
        if any(not value or not value.startswith("SYN-") for value in values):
            raise ValueError(f"Missing or non-synthetic {table} key.")
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate {table} primary key.")
    lead_ids = {row["lead_id"] for row in tables["leads"]}
    run_ids = {row["run_id"] for row in tables["runs"]}
    mentor_ids = {row["mentor_id"] for row in tables["mentors"]}
    if any(row["lead_id"] not in lead_ids or row["run_id"] not in run_ids for row in tables["events"]):
        raise ValueError("An event has an unknown lead or run reference.")
    if any(row["mentor_id"] and row["mentor_id"] not in mentor_ids for row in tables["leads"]):
        raise ValueError("A lead has an unknown mentor reference.")
    dates = {row["run_date"] for row in tables["runs"]}
    for value in dates:
        date.fromisoformat(value)
    if len(dates) != REFERENCE_DISTINCT_RUN_DATES:
        raise ValueError("Unexpected number of distinct synthetic run dates.")


def write_synthetic_backend(directory=DEFAULT_DIRECTORY):
    """Write public CSV fixtures. No network or original-workbook access."""
    tables = build_synthetic_backend()
    validate_backend(tables)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        with (directory / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=SCHEMAS[name])
            writer.writeheader()
            writer.writerows({**row, "synthetic": "true"} for row in rows)
    return tables


def load_backend(directory=DEFAULT_DIRECTORY):
    """Read the bundled public fixtures, converting the explicit marker to bool."""
    directory = Path(directory)
    tables = {}
    for name in SCHEMAS:
        with (directory / f"{name}.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            row["synthetic"] = row.get("synthetic") == "true"
        tables[name] = rows
    validate_backend(tables)
    return tables


def analyze_backend(tables=None):
    """Return full-volume synthetic analysis, never historical campaign results."""
    tables = load_backend() if tables is None else tables
    validate_backend(tables)
    lead_ids = {row["lead_id"] for row in tables["leads"]}
    run_ids = {row["run_id"] for row in tables["runs"]}
    mentor_ids = {row["mentor_id"] for row in tables["mentors"]}
    return {
        "synthetic": True,
        "description": "Row volumes match a reviewed historical snapshot; all row values, links, dates, distributions and outcomes are newly constructed.",
        "row_counts": {name: len(rows) for name, rows in tables.items()},
        "total_records": sum(len(rows) for rows in tables.values()),
        "distinct_run_dates": len({row["run_date"] for row in tables["runs"]}),
        "unique_primary_keys": {name: len({row[KEYS[name]] for row in rows}) for name, rows in tables.items()},
        "relationships": {
            "events_with_valid_lead": sum(row["lead_id"] in lead_ids for row in tables["events"]),
            "events_with_valid_run": sum(row["run_id"] in run_ids for row in tables["events"]),
            "leads_with_optional_mentor": sum(bool(row["mentor_id"]) for row in tables["leads"]),
            "unknown_mentor_references": sum(bool(row["mentor_id"]) and row["mentor_id"] not in mentor_ids for row in tables["leads"]),
            "distinct_leads_with_events": len({row["lead_id"] for row in tables["events"]}),
        },
        "event_type_counts": dict(Counter(row["event_type"] for row in tables["events"])),
        "lead_stage_counts": dict(Counter(row["stage"] for row in tables["leads"])),
        "mentor_demo_status_counts": dict(Counter(row["availability"] for row in tables["mentors"])),
        "external_actions": 0,
    }


if __name__ == "__main__":
    write_synthetic_backend()
    print(json.dumps(analyze_backend(), indent=2))
