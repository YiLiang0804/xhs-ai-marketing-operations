"""Build the explicit public-file release with neutral ZIP metadata."""

import argparse
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    '.github/workflows/checks.yml',
    '.gitignore',
    'PRIVACY.md',
    'README.md',
    'data/backend_snapshot_profile.json',
    'data/synthetic_backend/events.csv',
    'data/synthetic_backend/leads.csv',
    'data/synthetic_backend/mentors.csv',
    'data/synthetic_backend/runs.csv',
    'data/synthetic_content_drafts.json',
    'data/synthetic_event_brief.json',
    'data/synthetic_inquiries.json',
    'data/synthetic_posts.json',
    'data/synthetic_review_ledger.json',
    'docs/BACKEND_DATA_MODEL.md',
    'docs/CASE_STUDY.md',
    'docs/DEBUGGING_CASE_STUDY.md',
    'docs/DISCOVERY_AND_INTERACTION.md',
    'docs/EVALUATION.md',
    'docs/WALKTHROUGH.md',
    'docs/WORKFLOW_SPEC.md',
    'outputs/action_manifest.json',
    'outputs/backend_snapshot_profile.json',
    'outputs/content_drafts.json',
    'outputs/debug_replay.json',
    'outputs/discovery_plan.json',
    'outputs/duplicates.json',
    'outputs/interaction_verification.json',
    'outputs/leads.json',
    'outputs/metrics.json',
    'outputs/report.html',
    'outputs/reproducibility.txt',
    'outputs/review_queue.json',
    'outputs/synthetic_backend_analysis.json',
    'outputs/triage.md',
    'prompts/01_content_drafting.md',
    'prompts/02_inquiry_summary.md',
    'prompts/03_editorial_review.md',
    'prompts/04_discovery_review.md',
    'scripts/build_release.py',
    'tests/test_backend.py',
    'tests/test_discovery.py',
    'tests/test_recovery.py',
    'tests/test_release_privacy.py',
    'tests/test_workflow.py',
    'workflow/__init__.py',
    'workflow/__main__.py',
    'workflow/backend.py',
    'workflow/discovery.py',
    'workflow/pipeline.py',
    'workflow/recovery.py',
)
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def public_paths(root=ROOT):
    root = Path(root).resolve()
    result = []
    for relative in PUBLIC_FILES:
        path = root / relative
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Missing, symbolic or outside-root release item: {relative}")
        result.append((relative, path))
    return result


def build_release(output, root=ROOT):
    root = Path(root).resolve()
    output = Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError("Release archive must be written outside the project tree.")
    items = public_paths(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.comment = b""
        for relative, path in items:
            info = zipfile.ZipInfo("ai-content-lead-operations/" + relative, FIXED_ZIP_TIME)
            info.create_system = 0
            info.external_attr = 0x20
            info.compress_type = zipfile.ZIP_DEFLATED
            info.comment = b""
            info.extra = b""
            archive.writestr(info, path.read_bytes())
    return len(items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.out)
    print(f"Built public release with {count} approved files.")


if __name__ == "__main__":
    main()
