import copy
import json
import unittest
from pathlib import Path

from workflow.discovery import contact_context, plan_posts, verify_interaction


ROOT = Path(__file__).resolve().parents[1]


class DiscoveryReplayTests(unittest.TestCase):
    def setUp(self):
        self.posts = json.loads((ROOT / "data/synthetic_posts.json").read_text())
        self.post = self.posts[0]
        self.observation = {
            "synthetic": True,
            "observed_post_id": self.post["id"],
            "observed_author_id": self.post["author_id"],
            "comment_attempted": True,
            "complete_own_approved_comment_visible": True,
            "like_attempted": True,
            "liked_state_visible": True,
        }

    def test_fixture_plan_has_two_review_candidates_and_seven_holds(self):
        result = plan_posts(self.posts)
        self.assertEqual(sum(item["eligible_for_review"] for item in result), 2)
        self.assertEqual(sum(item["status"] == "held" for item in result), 7)
        self.assertTrue(all(item["status"] != "approved" for item in result))

    def test_sparse_profile_does_not_override_a_detailed_relevant_request(self):
        self.assertTrue(self.post["sparse_profile"])
        self.assertTrue(plan_posts([self.post])[0]["eligible_for_review"])

    def test_unread_profile_is_different_from_a_sparse_reviewed_profile(self):
        item = plan_posts([{**self.post, "profile_read": False}])[0]
        self.assertIn("author_profile_not_reviewed", item["reasons"])
        self.assertFalse(item["eligible_for_review"])

    def test_only_visible_home_feed_discovery_is_eligible(self):
        for source in ("saved_link", "search_result", "hidden_endpoint"):
            self.assertFalse(plan_posts([{**self.post, "source": source}])[0]["eligible_for_review"])

    def test_previous_contact_or_unknown_attempt_blocks_post_and_author_across_runs(self):
        for status in ("verified", "outcome_unknown"):
            for prior in (
                {"post_id": self.post["id"], "author_id": "SYN-OTHER", "status": status, "synthetic": True},
                {"post_id": "SYN-OTHER", "author_id": self.post["author_id"], "status": status, "synthetic": True},
            ):
                self.assertFalse(plan_posts([self.post], [prior])[0]["eligible_for_review"])

    def test_same_post_or_author_cannot_add_multiple_contact_candidates(self):
        copied = {**self.post, "id": "SYN-POST-COPY"}
        result = plan_posts([self.post, self.post, copied])
        self.assertEqual(sum(item["eligible_for_review"] for item in result), 1)

    def test_offer_only_unrelated_or_declined_records_are_held(self):
        for changed in ({"offer_only": True}, {"service_fit": False}, {"contact_declined": True}):
            self.assertFalse(plan_posts([{**self.post, **changed}])[0]["eligible_for_review"])

    def test_different_recipient_does_not_inherit_post_author_context(self):
        other = contact_context(self.post, "SYN-LIKER")
        self.assertFalse(other["is_post_author"])
        self.assertIsNone(other["known_request"])
        self.assertEqual(contact_context(self.post, self.post["author_id"])["known_request"], self.post["anchor"])

    def test_complete_own_comment_and_heart_at_correct_target_verify_pair(self):
        result = verify_interaction(self.post, self.observation)
        self.assertTrue(result["pair_verified"])
        self.assertEqual(result["comment_status"], "verified")
        self.assertEqual(result["like_status"], "verified")
        self.assertEqual(result["network_actions"], 0)

    def test_wrong_post_or_author_never_verifies(self):
        for field in ("observed_post_id", "observed_author_id"):
            result = verify_interaction(self.post, {**self.observation, field: "SYN-WRONG"})
            self.assertFalse(result["pair_verified"])
            self.assertEqual(result["comment_status"], "outcome_unknown")

    def test_send_click_empty_editor_or_count_change_is_not_delivery_proof(self):
        observation = {**self.observation, "complete_own_approved_comment_visible": False, "send_clicked": True, "editor_empty": True, "comment_count_increased": True}
        result = verify_interaction(self.post, observation)
        self.assertEqual(result["comment_status"], "outcome_unknown")
        self.assertFalse(result["can_attempt_comment"])
        self.assertFalse(result["can_attempt_like"])
        self.assertFalse(result["pair_verified"])

    def test_comment_confirmation_and_like_confirmation_are_separate(self):
        result = verify_interaction(self.post, {**self.observation, "liked_state_visible": False})
        self.assertEqual(result["comment_status"], "verified")
        self.assertEqual(result["like_status"], "outcome_unknown")
        self.assertFalse(result["pair_verified"])

    def test_unlabeled_inputs_are_rejected(self):
        bad = copy.deepcopy(self.post)
        del bad["synthetic"]
        with self.assertRaises(ValueError):
            plan_posts([bad])
        with self.assertRaises(ValueError):
            verify_interaction(self.post, {**self.observation, "synthetic": False})


if __name__ == "__main__":
    unittest.main()
