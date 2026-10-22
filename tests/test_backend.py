import copy
import tempfile
import unittest

from workflow.backend import (
    REFERENCE_COUNTS, analyze_backend, build_synthetic_backend,
    load_backend, validate_backend, write_synthetic_backend,
)


class BackendVolumeTests(unittest.TestCase):
    def setUp(self):
        self.tables = build_synthetic_backend()

    def test_full_record_volumes_and_distinct_run_dates(self):
        result = analyze_backend(self.tables)
        self.assertEqual(result["row_counts"], REFERENCE_COUNTS)
        self.assertEqual(result["total_records"], 2511)
        self.assertEqual(result["distinct_run_dates"], 29)

    def test_all_foreign_keys_resolve_and_every_lead_has_history(self):
        links = analyze_backend(self.tables)["relationships"]
        self.assertEqual(links["events_with_valid_lead"], 1771)
        self.assertEqual(links["events_with_valid_run"], 1771)
        self.assertEqual(links["distinct_leads_with_events"], 606)
        self.assertEqual(links["unknown_mentor_references"], 0)

    def test_optional_mentor_is_allowed_but_unknown_mentor_is_not(self):
        self.assertTrue(any(not row["mentor_id"] for row in self.tables["leads"]))
        invalid = copy.deepcopy(self.tables)
        invalid["leads"][0]["mentor_id"] = "SYN-MENTOR-UNKNOWN"
        with self.assertRaises(ValueError):
            validate_backend(invalid)

    def test_duplicate_primary_key_is_rejected(self):
        invalid = copy.deepcopy(self.tables)
        invalid["events"][1]["event_id"] = invalid["events"][0]["event_id"]
        with self.assertRaises(ValueError):
            validate_backend(invalid)

    def test_unknown_event_lead_or_run_is_rejected(self):
        for key in ("lead_id", "run_id"):
            invalid = copy.deepcopy(self.tables)
            invalid["events"][0][key] = "SYN-UNKNOWN"
            with self.assertRaises(ValueError):
                validate_backend(invalid)

    def test_unlabeled_and_extra_private_fields_are_rejected(self):
        for change in ("unlabeled", "extra_field"):
            invalid = copy.deepcopy(self.tables)
            if change == "unlabeled":
                invalid["leads"][0]["synthetic"] = False
            else:
                invalid["leads"][0]["private_note"] = "Not part of the public schema"
            with self.assertRaises(ValueError):
                validate_backend(invalid)

    def test_wrong_row_volume_or_date_count_is_rejected(self):
        invalid = copy.deepcopy(self.tables)
        invalid["leads"].pop()
        with self.assertRaises(ValueError):
            validate_backend(invalid)
        invalid = copy.deepcopy(self.tables)
        for row in invalid["runs"]:
            row["run_date"] = "2030-01-01"
        with self.assertRaises(ValueError):
            validate_backend(invalid)

    def test_csv_roundtrip_preserves_public_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            write_synthetic_backend(directory)
            self.assertEqual(load_backend(directory), self.tables)

    def test_reproduction_is_deterministic_and_no_external_action_is_claimed(self):
        self.assertEqual(build_synthetic_backend(), self.tables)
        result = analyze_backend(self.tables)
        self.assertTrue(result["synthetic"])
        self.assertEqual(result["external_actions"], 0)


if __name__ == "__main__":
    unittest.main()
