import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_law", ROOT / "tools" / "check_law.py")
check_law = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_law)


def act(status="obowiązujący", amending=(), **extra):
    """Odpowiedź API w uproszczonej postaci."""
    data = {"changeDate": "2026-01-01", "status": status,
            "references": {"Akty zmieniające": [{"id": i, "date": d} for i, d in amending]}}
    data.update(extra)
    return data


class DifferencesTests(unittest.TestCase):
    groups = ("Akty zmieniające",)

    def snap(self, **kw):
        return check_law.snapshot(act(**kw), self.groups)

    def test_no_changes(self):
        s = {"DU/1994/214": self.snap(amending=[("DU/2025/1", "2026-01-01")])}
        self.assertEqual(check_law.differences(s, s), [])

    def test_new_amending_act_is_reported_with_its_date(self):
        old = {"DU/1994/214": self.snap(amending=[("DU/2025/1", "2026-01-01")])}
        new = {"DU/1994/214": self.snap(amending=[("DU/2025/1", "2026-01-01"), ("DU/2026/9", "2027-01-01")])}
        found = check_law.differences(old, new)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][2], "DU/2026/9")
        self.assertIn("2027-01-01", found[0][1])

    def test_moved_effective_date_status_change_and_removal(self):
        old = {"DU/1994/214": self.snap(amending=[("DU/2025/1", "2026-01-01"), ("DU/2025/2", "2026-02-01")])}
        new = {"DU/1994/214": self.snap(status="uchylony", amending=[("DU/2025/1", "2026-06-01")])}
        text = " | ".join(change[1] for change in check_law.differences(old, new))
        self.assertIn("status", text)
        self.assertIn("z 2026-01-01 na 2026-06-01", text)
        self.assertIn("zniknął", text)

    def test_unwatched_before_is_reported(self):
        self.assertEqual(len(check_law.differences({}, {"DU/1994/214": self.snap()})), 1)


class ReportTests(unittest.TestCase):
    def test_empty_when_nothing_to_report(self):
        self.assertEqual(check_law.render([], [], {}, date(2026, 1, 1)), "")

    def test_report_lists_changes_titles_and_deadlines(self):
        changes = [("DU/1994/214", "nowy wpis w grupie „Akty zmieniające”: DU/2026/9 (data: 2027-01-01)", "DU/2026/9")]
        text = check_law.render(changes, ["Progi wygasają 30.11.2026."], {"DU/2026/9": "Ustawa o zmianie ustawy"}, date(2026, 11, 1))
        self.assertIn("Ustawa o zmianie ustawy", text)
        self.assertIn("Progi wygasają", text)
        self.assertIn("check_law.py --accept", text)

    def test_deadlines_warn_before_and_after_expiry(self):
        before = check_law.deadlines(date(2026, 11, 5))
        after = check_law.deadlines(date(2026, 12, 5))
        self.assertTrue(any("wygasają 30.11.2026" in line for line in before))
        self.assertTrue(any("wygasły 30.11.2026" in line for line in after))


class MainTests(unittest.TestCase):
    def test_baseline_in_repo_covers_all_watched_acts(self):
        baseline = json.loads(Path(check_law.BASELINE).read_text(encoding="utf-8"))
        self.assertEqual(set(baseline["acts"]), set(check_law.WATCHED))

    def test_run_with_fake_api_reports_new_amendment_without_network(self):
        baseline = json.loads(Path(check_law.BASELINE).read_text(encoding="utf-8"))["acts"]

        def fake(eli):
            if eli == "DU/2099/1":
                return {"title": "Ustawa testowa"}
            data = {"changeDate": baseline[eli]["changeDate"], "status": baseline[eli]["status"], "references": {
                group: [{"id": i, "date": d} for i, d in items.items()] for group, items in baseline[eli]["references"].items()}}
            if eli == "DU/1994/214":
                data["references"]["Akty zmieniające"].append({"id": "DU/2099/1", "date": "2100-01-01"})
            return data

        with tempfile.TemporaryDirectory() as folder:
            report = str(Path(folder) / "r.md")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(check_law.main(["x", "--report", report], get=fake, today=date(2026, 11, 1)), 0)
            text = Path(report).read_text(encoding="utf-8")
        self.assertIn("DU/2099/1", text)
        self.assertIn("Ustawa testowa", text)


if __name__ == "__main__":
    unittest.main()
