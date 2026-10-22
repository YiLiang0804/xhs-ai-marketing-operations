"""Offline reconstruction of feed discovery and interaction verification.

All observations are supplied synthetic fixtures. This module does not browse,
search, scrape, publish, like, or send. Its simplified public rules are not the
private browser workflow, and its examples are not historical incident logs.
"""


def _require_synthetic(rows):
    for row in rows:
        if row.get("synthetic") is not True:
            raise ValueError("Discovery replay accepts labeled synthetic records only.")


def plan_posts(posts, history=()):
    """Return a reasoned review plan from operator-supplied post observations.

    ``history`` contains fictional contact-event dictionaries with ``post_id``
    and ``author_id``. Verified and unresolved attempts both block new contact.
    Sparse profile history is not by itself a reason to reject a coherent post.
    """
    _require_synthetic(posts)
    _require_synthetic(history)
    prior_posts = {row["post_id"] for row in history}
    prior_authors = {row["author_id"] for row in history}
    seen_posts, planned_authors, items = set(), set(), []
    for post in posts:
        post_id, author_id = post["id"], post["author_id"]
        reasons = []
        if post_id in prior_posts or author_id in prior_authors:
            reasons.append("prior_contact_or_unresolved_attempt")
        if post_id in seen_posts:
            reasons.append("duplicate_post_in_batch")
        if author_id in planned_authors:
            reasons.append("author_already_in_review_plan")
        if post.get("source") != "homepage_visible_card":
            reasons.append("not_discovered_from_visible_home_feed")
        if post.get("detail_read") is not True:
            reasons.append("post_detail_not_reviewed")
        if post.get("profile_read") is not True:
            reasons.append("author_profile_not_reviewed")
        if post.get("recency_checked") is not True:
            reasons.append("recency_not_confirmed")
        if post.get("explicit_need") is not True:
            reasons.append("no_explicit_relevant_request")
        if post.get("service_fit") is not True:
            reasons.append("service_fit_not_confirmed")
        if post.get("offer_only") is True:
            reasons.append("offer_or_result_sharing_only")
        if post.get("contact_declined") is True:
            reasons.append("contact_declined")
        if not post.get("anchor", "").strip():
            reasons.append("missing_post_context_anchor")
        eligible = not reasons
        seen_posts.add(post_id)
        if eligible:
            planned_authors.add(author_id)
        items.append({
            "post_id": post_id,
            "author_id": author_id,
            "synthetic": True,
            "source": post.get("source"),
            "status": "pending_review" if eligible else "held",
            "eligible_for_review": eligible,
            "reasons": reasons or ["relevant_request_with_reviewed_context"],
            "anchor": post.get("anchor"),
            "draft": f"Hi, happy to discuss your {post['anchor']} question if useful." if eligible else None,
            "draft_method": "deterministic_context_template",
            "sparse_profile": post.get("sparse_profile", False),
            "note": "Synthetic planning only; no communication is approved or sent.",
        })
    return items


def contact_context(post, recipient_id):
    """Do not copy a post author's background to a different person who liked it."""
    _require_synthetic([post])
    is_author = recipient_id == post["author_id"]
    return {
        "synthetic": True,
        "recipient_id": recipient_id,
        "is_post_author": is_author,
        "known_request": post.get("anchor") if is_author else None,
        "next_step": "Review the stated request." if is_author else "Ask about this person's own needs; do not inherit the post author's background.",
    }


def verify_interaction(post, observation):
    """Evaluate supplied evidence, never execute an interaction.

    A click, an empty editor or a changed comment count is not proof of delivery.
    The complete own approved comment must be visible under the correct post and
    author. An unresolved attempt blocks another attempt. Like verification is
    evaluated only after comment verification. Attempt flags describe this
    verification layer only, not authorization, history or platform readiness.
    """
    _require_synthetic([post, observation])
    target_matches = (
        observation.get("observed_post_id") == post["id"]
        and observation.get("observed_author_id") == post["author_id"]
    )
    attempted = observation.get("comment_attempted") is True or observation.get("send_clicked") is True
    comment_verified = target_matches and observation.get("complete_own_approved_comment_visible") is True
    comment_status = "verified" if comment_verified else "outcome_unknown" if attempted else "not_attempted"
    like_verified = comment_verified and observation.get("liked_state_visible") is True
    like_attempted = observation.get("like_attempted") is True
    if like_attempted and not comment_verified:
        like_status = "blocked_comment_not_verified"
    elif like_verified:
        like_status = "verified"
    else:
        like_status = "outcome_unknown" if like_attempted else "not_attempted"
    reasons = []
    if not target_matches:
        reasons.append("target_identity_not_confirmed")
    if attempted and not comment_verified:
        reasons.append("delivery_not_proven_do_not_resend")
    if like_attempted and not comment_verified:
        reasons.append("like_evidence_cannot_complete_an_unverified_comment")
    return {
        "synthetic": True,
        "post_id": post["id"],
        "target_matches": target_matches,
        "comment_status": comment_status,
        "like_status": like_status,
        "pair_verified": comment_verified and like_verified,
        "can_attempt_comment": not attempted and not comment_verified and target_matches,
        "can_attempt_like": comment_verified and not like_attempted and not like_verified,
        "eligibility_note": "Verification-layer state only; authorization, history, checkpoint and platform readiness are separate checks.",
        "reasons": reasons,
        "network_actions": 0,
    }
