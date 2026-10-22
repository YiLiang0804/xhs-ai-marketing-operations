"""Offline reconstruction of retry-state debugging. No browser operations."""

from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True)
class RecoveryRecord:
    phase: str = "idle"
    retry_budget_reserved: bool = False
    request_id: str | None = None
    request_submitted: bool = False
    error_class: str | None = None
    stopped: bool = True
    pending_interlock: bool = True
    completed_pairs: int = 2
    deadline: str = "2030-01-01T09:00:00Z"
    audit: tuple[str, ...] = ()


def record_reservation(state):
    """Record budget consumption; this does not execute a retry."""
    if state.retry_budget_reserved:
        raise ValueError("The recovery budget is already reserved; no second reservation.")
    return replace(state, phase="reserved", retry_budget_reserved=True,
                   audit=state.audit + ("budget_reserved_not_execution",))


def record_not_submitted(state):
    """A conditional action that was never submitted is not an attempted action."""
    if state.phase != "reserved":
        raise ValueError("Expected an existing reservation.")
    return replace(state, audit=state.audit + ("conditional_request_not_submitted",))


def record_submission(state, request_id):
    """Record an acknowledged submission, without invoking any tool."""
    if state.phase != "reserved" or state.request_submitted:
        raise ValueError("A single reserved request may be recorded once.")
    if not request_id:
        raise ValueError("An explicit synthetic request identity is required.")
    return replace(state, phase="attempted", request_id=request_id, request_submitted=True,
                   audit=state.audit + ("request_submission_recorded",))


def record_result(state, request_id, result, execution_acknowledged):
    """Only a matching, acknowledged execution can resolve a retry's outcome."""
    if state.phase != "attempted" or request_id != state.request_id:
        raise ValueError("Result must match the unresolved submitted request.")
    if result not in {"success", "code_error", "ordinary_load_failure", "tool_review_denial", "unknown"}:
        raise ValueError("Unknown result classification.")
    if result == "success" and execution_acknowledged:
        phase, error_class = "succeeded", None
    elif result in {"code_error", "ordinary_load_failure"} and execution_acknowledged:
        phase, error_class = "failed", result
    else:
        phase = "outcome_unknown"
        error_class = result if result != "success" else "unacknowledged_execution"
    # Never release stop flags, pending interlocks, budget, history, or deadline.
    return replace(state, phase=phase, error_class=error_class,
                   audit=state.audit + (f"result_recorded:{phase}:{error_class or 'none'}",))


def record_observation(state, healthy=False, denied=False):
    """A screenshot/observation cannot prove an earlier action executed."""
    if healthy and denied:
        raise ValueError("A denied observation cannot also be a healthy observation.")
    label = "observation_denied" if denied else "healthy_observation" if healthy else "observation_only"
    return replace(state, audit=state.audit + (label,))


def replay_debug_case():
    initial = RecoveryRecord()
    reserved = record_reservation(initial)
    attempted = record_submission(reserved, "SYN-REQUEST-01")
    unknown = record_result(attempted, "SYN-REQUEST-01", "tool_review_denial", False)
    observed = record_observation(unknown, healthy=True)
    return {
        "synthetic": True,
        "method": "standalone_offline_reconstruction",
        "historical_basis": "Retry reservation versus execution ambiguity; observation is not execution acknowledgement.",
        "steps": [{"label": label, **asdict(state)} for label, state in [
            ("initial", initial), ("budget reserved", reserved), ("submission recorded", attempted),
            ("execution outcome unknown", unknown), ("later observation does not resolve execution", observed),
        ]],
        "invariants": {
            "budget_remains_reserved": observed.retry_budget_reserved,
            "stop_remains_set": observed.stopped,
            "pending_interlock_remains_set": observed.pending_interlock,
            "completed_history_preserved": observed.completed_pairs == initial.completed_pairs,
            "deadline_preserved": observed.deadline == initial.deadline,
            "healthy_observation_does_not_claim_success": observed.phase == "outcome_unknown",
        },
        "browser_calls": 0,
        "platform_actions": 0,
    }
