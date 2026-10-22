import unittest

from workflow.recovery import (
    RecoveryRecord, record_not_submitted, record_observation, record_reservation,
    record_result, record_submission, replay_debug_case,
)


class RecoveryDebugTests(unittest.TestCase):
    def setUp(self):
        self.initial = RecoveryRecord()
        self.reserved = record_reservation(self.initial)
        self.attempted = record_submission(self.reserved, "SYN-REQUEST-01")

    def test_reservation_consumes_budget_but_is_not_execution(self):
        self.assertEqual(self.reserved.phase, "reserved")
        self.assertTrue(self.reserved.retry_budget_reserved)
        self.assertFalse(self.reserved.request_submitted)

    def test_repeated_reservation_is_rejected(self):
        with self.assertRaises(ValueError):
            record_reservation(self.reserved)

    def test_unsubmitted_request_adds_neither_attempt_nor_denial(self):
        state = record_not_submitted(self.reserved)
        self.assertEqual(state.phase, "reserved")
        self.assertFalse(state.request_submitted)
        self.assertIsNone(state.error_class)

    def test_submission_is_recorded_once(self):
        self.assertEqual(self.attempted.phase, "attempted")
        with self.assertRaises(ValueError):
            record_submission(self.attempted, "SYN-REQUEST-01")

    def test_result_must_match_request_identity(self):
        with self.assertRaises(ValueError):
            record_result(self.attempted, "SYN-OTHER", "success", True)

    def test_no_result_before_acknowledged_submission(self):
        with self.assertRaises(ValueError):
            record_result(self.reserved, "SYN-REQUEST-01", "success", True)

    def test_unacknowledged_success_is_unknown(self):
        state = record_result(self.attempted, "SYN-REQUEST-01", "success", False)
        self.assertEqual(state.phase, "outcome_unknown")

    def test_review_denial_is_distinct_from_loading_failure(self):
        state = record_result(self.attempted, "SYN-REQUEST-01", "tool_review_denial", False)
        self.assertEqual(state.error_class, "tool_review_denial")
        self.assertEqual(state.phase, "outcome_unknown")

    def test_healthy_observation_does_not_resolve_unknown_action(self):
        state = record_result(self.attempted, "SYN-REQUEST-01", "unknown", False)
        after = record_observation(state, healthy=True)
        self.assertEqual(after.phase, "outcome_unknown")
        self.assertEqual(after.request_id, state.request_id)

    def test_denied_observation_is_not_a_retry_attempt(self):
        state = record_observation(self.reserved, denied=True)
        self.assertEqual(state.phase, "reserved")
        self.assertFalse(state.request_submitted)

    def test_error_types_remain_separate(self):
        for error in ("code_error", "ordinary_load_failure"):
            state = record_result(self.attempted, "SYN-REQUEST-01", error, True)
            self.assertEqual(state.error_class, error)
            self.assertEqual(state.phase, "failed")

    def test_success_does_not_implicitly_resume_or_change_history(self):
        state = record_result(self.attempted, "SYN-REQUEST-01", "success", True)
        self.assertEqual(state.phase, "succeeded")
        self.assertTrue(state.stopped)
        self.assertTrue(state.pending_interlock)
        self.assertTrue(state.retry_budget_reserved)
        self.assertEqual(state.completed_pairs, self.initial.completed_pairs)
        self.assertEqual(state.deadline, self.initial.deadline)

    def test_unknown_cannot_be_resubmitted_or_reclassified_by_a_later_snapshot(self):
        state = record_result(self.attempted, "SYN-REQUEST-01", "unknown", False)
        with self.assertRaises(ValueError):
            record_submission(state, "SYN-REQUEST-02")
        with self.assertRaises(ValueError):
            record_result(state, "SYN-REQUEST-01", "success", True)

    def test_replay_preserves_all_invariants_without_browser_calls(self):
        result = replay_debug_case()
        self.assertTrue(all(result["invariants"].values()))
        self.assertEqual(result["browser_calls"], 0)
        self.assertEqual(result["platform_actions"], 0)


if __name__ == "__main__":
    unittest.main()
