import json
from pathlib import Path
import shutil
import secrets
import tempfile
import unittest
import zipfile

from scripts.build_release import FIXED_ZIP_TIME, PUBLIC_FILES, ROOT, build_release


class PublicReleasePrivacyTests(unittest.TestCase):
    def test_archive_contains_only_explicitly_approved_files(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "release.zip"
            build_release(archive_path)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(set(archive.namelist()), {"ai-content-lead-operations/" + name for name in PUBLIC_FILES})
                for name in archive.namelist():
                    self.assertNotIn("__pycache__", name)
                    self.assertFalse(name.endswith((".pyc", ".xlsx", ".har", ".log")))

    def test_archive_has_fixed_timestamps_and_no_extra_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "release.zip"
            build_release(archive_path)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(archive.comment, b"")
                for info in archive.infolist():
                    self.assertEqual(info.date_time, FIXED_ZIP_TIME)
                    self.assertEqual(info.extra, b"")
                    self.assertEqual(info.comment, b"")
                    self.assertEqual(info.create_system, 0)

    def test_unlisted_private_runtime_and_cache_files_are_not_packaged(self):
        with tempfile.TemporaryDirectory() as directory:
            canary = "PRIVATE_" + secrets.token_hex(16)
            root = Path(directory) / "project"
            root.mkdir()
            for relative in PUBLIC_FILES:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, destination)
            for relative in ["private/raw.txt", "runtime/ledger.json", "workflow/__pycache__/private.pyc"]:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(canary)
            archive_path = Path(directory) / "release.zip"
            build_release(archive_path, root)
            with zipfile.ZipFile(archive_path) as archive:
                for name in archive.namelist():
                    self.assertNotIn(canary.encode(), archive.read(name))

    def test_exact_historical_operating_date_is_withheld_and_small_groups_are_combined(self):
        profile = json.loads((ROOT / "data/backend_snapshot_profile.json").read_text())
        self.assertIsNone(profile["snapshot_date"])
        self.assertIn("withheld", profile["snapshot_period"])
        self.assertTrue(all(row["records"] >= 5 or row["label"] == "other_states" for row in profile["run_status_distribution"]))
        self.assertEqual(sum(row["records"] for row in profile["run_status_distribution"]), 39)

    def test_allowlisted_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            root.mkdir()
            outside = Path(directory) / "outside.txt"
            outside.write_text("PRIVATE_TEST_CANARY")
            for relative in PUBLIC_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if relative == "README.md":
                    try:
                        path.symlink_to(outside)
                    except OSError:
                        self.skipTest("Symbolic-link creation is unavailable in this environment.")
                else:
                    shutil.copyfile(ROOT / relative, path)
            with self.assertRaises(ValueError):
                build_release(Path(directory) / "release.zip", root)


if __name__ == "__main__":
    unittest.main()
