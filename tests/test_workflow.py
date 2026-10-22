import copy
import tempfile
import unittest
from pathlib import Path

from workflow.pipeline import (
    ROOT, DEMO_DATE, approve, approved_engagement_count, build_outputs,
    deduplicate, export_outputs, load_ledger, prioritize, read_json, render_report, write_json,
)


class WorkflowAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.rows = read_json(ROOT / "data/synthetic_inquiries.json")
        self.drafts = read_json(ROOT / "data/synthetic_content_drafts.json")
        self.ledger = read_json(ROOT / "data/synthetic_review_ledger.json")

    def result(self, ledger=None):
        return build_outputs(self.rows, self.drafts, self.ledger if ledger is None else ledger)

    def test_fixture_accounting_and_empty_baseline_manifest(self):
        result = self.result()
        self.assertEqual(result["metrics"]["input_records"], 12)
        self.assertEqual(result["metrics"]["unique_inquiries"], 11)
        self.assertEqual(result["metrics"]["duplicates_removed"], 1)
        self.assertEqual(result["metrics"]["eligible_review_items"], 5)
        self.assertEqual(result["metrics"]["blocked_inquiries"], 6)
        self.assertEqual(result["action_manifest"], [])
        self.assertTrue(all(row["status"] == "pending_review" for row in result["review_queue"]))

    def test_duplicate_id_and_normalized_text_do_not_add_review_items(self):
        same_id = {**self.rows[0], "message": "Different text but the same inquiry identity"}
        same_text = {**self.rows[0], "id": "SYN-099", "message": "  " + self.rows[0]["message"] + "  "}
        unique, duplicates = deduplicate([self.rows[0], same_id, same_text])
        self.assertEqual(len(unique), 1)
        self.assertEqual(len(duplicates), 2)

    def test_score_is_explainable_and_missing_information_is_preserved(self):
        for row in self.result()["leads"]:
            self.assertEqual(row["priority_score"], sum(reason["points"] for reason in row["score_reasons"]))
        incomplete = prioritize(self.rows[1])
        self.assertIsNone(incomplete["timeline"])
        self.assertIn("timeline", incomplete["missing_information"])
        self.assertIn("Ask for missing", incomplete["next_step"])

    def test_high_score_does_not_override_permission_or_terminal_stage(self):
        high_score = {**self.rows[0], "followup_permission": False}
        self.assertEqual(prioritize(high_score)["priority_score"], 100)
        self.assertFalse(prioritize(high_score)["eligible_for_review"])
        for stage in ("closed", "hold", "handed_off"):
            self.assertFalse(prioritize({**self.rows[0], "stage": stage})["eligible_for_review"])

    def test_blocked_item_or_missing_reviewer_cannot_be_approved(self):
        queue = self.result()["review_queue"]
        with self.assertRaises(ValueError):
            approve("SYN-008", "operator", self.ledger, queue, DEMO_DATE)
        with self.assertRaises(ValueError):
            approve("SYN-001", " ", self.ledger, queue, DEMO_DATE)

    def test_daily_cap_persists_across_reload_and_repeat_approval_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            queue = self.result()["review_queue"]
            ledger = approve("SYN-001", "operator", self.ledger, queue, DEMO_DATE)
            write_json(path, ledger)
            reloaded = load_ledger(path)
            self.assertEqual(approved_engagement_count(reloaded, DEMO_DATE), 10)
            self.assertEqual(self.result(reloaded)["metrics"]["remaining_review_allowance"], 0)
            self.assertEqual(approve("SYN-001", "operator", reloaded, queue, DEMO_DATE), reloaded)
            self.assertEqual(approve("SYN-001", "operator", reloaded, queue, "2026-01-13"), reloaded)
            with self.assertRaises(ValueError):
                approve("SYN-002", "operator", reloaded, queue, DEMO_DATE)

    def test_new_date_has_separate_allowance_for_a_different_inquiry(self):
        queue = self.result()["review_queue"]
        ledger = approve("SYN-002", "operator", self.ledger, queue, "2026-01-13")
        self.assertEqual(approved_engagement_count(ledger, "2026-01-13"), 1)
        self.assertEqual(approved_engagement_count(ledger, DEMO_DATE), 9)

    def test_no_unreviewed_item_enters_approval_manifest(self):
        queue = self.result()["review_queue"]
        ledger = approve("SYN-004", "operator", self.ledger, queue, DEMO_DATE)
        self.assertEqual([row["id"] for row in self.result(ledger)["action_manifest"]], ["SYN-004"])

    def test_approved_state_is_visible_in_json_markdown_and_html(self):
        queue = self.result()["review_queue"]
        ledger = approve("SYN-001", "operator", self.ledger, queue, DEMO_DATE)
        result = self.result(ledger)
        row = next(row for row in result["leads"] if row["id"] == "SYN-001")
        self.assertEqual(row["review_status"], "approved")
        self.assertIn("<td>approved</td>", render_report(result))
        with tempfile.TemporaryDirectory() as directory:
            export_outputs(result, directory)
            line = next(line for line in (Path(directory) / "triage.md").read_text().splitlines() if "SYN-001" in line)
            self.assertIn("approved", line)

    def test_unlabeled_input_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        del rows[0]["synthetic"]
        with self.assertRaises(ValueError):
            build_outputs(rows, self.drafts, self.ledger)

    def test_deterministic_outputs(self):
        self.assertEqual(self.result(), self.result())

    def test_report_leads_with_real_snapshot_scale_and_separates_small_fixtures(self):
        profile = read_json(ROOT / "data/backend_snapshot_profile.json")
        from workflow.backend import analyze_backend
        result = build_outputs(self.rows, self.drafts, self.ledger, snapshot_profile=profile, backend_analysis=analyze_backend())
        report = render_report(result)
        for count in ("606", "1,771", "39", "95"):
            self.assertIn(f"<b>{count}</b>", report)
        self.assertLess(report.index("<b>1,771</b>"), report.index("<details>"))
        self.assertIn("small_regression_fixtures_only", result["metrics"]["metric_scope"])

    def test_synthetic_backend_volumes_match_the_separate_historical_profile(self):
        from workflow.backend import analyze_backend
        profile = read_json(ROOT / "data/backend_snapshot_profile.json")
        names = {"leads": "leads", "outreach-events": "events", "daily-runs": "runs", "mentor-directory": "mentors"}
        expected = {names[row["name"]]: row["records"] for row in profile["tables"]}
        self.assertEqual(analyze_backend()["row_counts"], expected)


if __name__ == "__main__":
    unittest.main()
