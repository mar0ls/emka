import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import urllib.parse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_law", ROOT / "tools" / "check_law.py")
check_law = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_law)

GROUPS = ("Akty zmieniające",)


def act(status="obowiązujący", amending=(), change_date="2026-01-01"):
    """Odpowiedź API w uproszczonej postaci."""
    return {"changeDate": change_date, "status": status,
            "references": {"Akty zmieniające": [{"id": i, "date": d} for i, d in amending]}}


def snap(text_hash=None, **kw):
    return check_law.snapshot(act(**kw), GROUPS, text_hash)


class DifferencesTests(unittest.TestCase):
    def test_no_changes(self):
        s = {"DU/1994/214": snap(amending=[("DU/2025/1", "2026-01-01")], text_hash="a")}
        self.assertEqual(check_law.differences(s, s, strict={"DU/1994/214"}), [])

    def test_new_amending_act_is_reported_with_its_date(self):
        old = {"DU/1994/214": snap(amending=[("DU/2025/1", "2026-01-01")])}
        new = {"DU/1994/214": snap(amending=[("DU/2025/1", "2026-01-01"), ("DU/2026/9", "2027-01-01")])}
        found = check_law.differences(old, new)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][2], "DU/2026/9")
        self.assertIn("2027-01-01", found[0][1])

    def test_moved_effective_date_status_change_and_removal(self):
        old = {"DU/1994/214": snap(amending=[("DU/2025/1", "2026-01-01"), ("DU/2025/2", "2026-02-01")])}
        new = {"DU/1994/214": snap(status="uchylony", amending=[("DU/2025/1", "2026-06-01")])}
        text = " | ".join(change[1] for change in check_law.differences(old, new))
        self.assertIn("status", text)
        self.assertIn("z 2026-01-01 na 2026-06-01", text)
        self.assertIn("zniknął", text)

    def test_unwatched_before_is_reported(self):
        self.assertEqual(len(check_law.differences({}, {"DU/1994/214": snap()})), 1)

    def test_text_change_without_new_amending_act_is_reported_for_strict_acts(self):
        old = {"DU/1994/214": snap(text_hash="aaa")}
        new = {"DU/1994/214": snap(text_hash="bbb")}
        found = check_law.differences(old, new, strict={"DU/1994/214"})
        self.assertEqual(len(found), 1)
        self.assertIn("tekst ujednolicony", found[0][1])
        self.assertEqual(check_law.differences(old, new), [], "bez trybu strict zmiana tekstu jest pomijana")

    def test_change_date_alone_is_reported_for_strict_acts(self):
        old = {"DU/2005/734": snap(change_date="2020-09-18")}
        new = {"DU/2005/734": snap(change_date="2026-12-01")}
        found = check_law.differences(old, new, strict={"DU/2005/734"})
        self.assertEqual(len(found), 1)
        self.assertIn("2026-12-01", found[0][1])


class NoticeTests(unittest.TestCase):
    def test_only_new_notices_are_reported(self):
        old = {"przychodu odpowiadających": {"MP/2026/839": "Komunikat A"}}
        new = {"przychodu odpowiadających": {"MP/2026/839": "Komunikat A", "MP/2026/1200": "Komunikat B"},
               "najniższej emerytury": {}}
        found = check_law.notice_differences(old, new)
        self.assertEqual(found, [("przychodu odpowiadających", "nowy komunikat MP/2026/1200: Komunikat B")])

    def test_search_path_is_url_encoded(self):
        path = check_law.notice_search("przychodu odpowiadających", 2026)
        self.assertTrue(path.startswith("search?"))
        self.assertIn("publisher=MP", path)
        self.assertNotIn(" ", path)

    def test_consolidated_text_path_prefers_type_u(self):
        data = {"texts": [{"fileName": "a.pdf", "type": "O"}, {"fileName": "b.pdf", "type": "U"}]}
        self.assertEqual(check_law.consolidated_text_path("DU/1/2", data), "DU/1/2/text/U/b.pdf")
        self.assertIsNone(check_law.consolidated_text_path("DU/1/2", {"texts": []}))


class ReportTests(unittest.TestCase):
    def test_empty_when_nothing_to_report(self):
        self.assertEqual(check_law.render([], [], {}, date(2026, 1, 1)), "")

    def test_report_lists_changes_titles_notices_and_deadlines(self):
        changes = [("DU/1994/214", "nowy wpis w grupie „Akty zmieniające”: DU/2026/9 (data: 2027-01-01)", "DU/2026/9")]
        notices = [("przychodu odpowiadających", "nowy komunikat MP/2026/1200: Komunikat B")]
        text = check_law.render(changes, ["Progi wygasają 30.11.2026."], {"DU/2026/9": "Ustawa o zmianie ustawy"},
                                date(2026, 11, 1), notices)
        self.assertIn("Ustawa o zmianie ustawy", text)
        self.assertIn("Progi wygasają", text)
        self.assertIn("MP/2026/1200", text)
        self.assertIn("check_law.py --accept", text)

    def test_notices_alone_are_enough_for_a_report(self):
        text = check_law.render([], [], {}, date(2026, 11, 1), [("najniższej emerytury", "nowy komunikat MP/2027/1: X")])
        self.assertIn("Nowe komunikaty", text)

    def test_deadlines_warn_before_and_after_expiry(self):
        before = check_law.deadlines(date(2026, 11, 5))
        after = check_law.deadlines(date(2026, 12, 5))
        self.assertTrue(any("wygasają 30.11.2026" in line for line in before))
        self.assertTrue(any("wygasły 30.11.2026" in line for line in after))


class MainTests(unittest.TestCase):
    baseline = json.loads(Path(check_law.BASELINE).read_text(encoding="utf-8"))

    def test_baseline_in_repo_covers_everything_watched(self):
        self.assertEqual(set(self.baseline["acts"]), set(check_law.WATCHED))
        self.assertEqual(set(self.baseline["notices"]), set(check_law.NOTICES))
        self.assertTrue(self.baseline["acts"]["DU/1994/214"]["textHash"], "ustawa mundurowa ma skrót tekstu ujednoliconego")

    def fake_api(self, new_amendment=False, new_notice=False, new_text=False):
        baseline = self.baseline

        def get(path):
            if path.startswith("search?"):
                query = urllib.parse.parse_qs(path[len('search?'):])['title'][0]
                items = [{"ELI": eli, "title": title} for eli, title in baseline["notices"][query].items()]
                if new_notice:
                    items.append({"ELI": "MP/2099/7", "title": "Komunikat testowy"})
                return {"items": items}
            if path == "DU/2099/1":
                return {"title": "Ustawa testowa"}
            old = baseline["acts"][path]
            data = {"changeDate": old["changeDate"], "status": old["status"], "texts": [{"type": "U", "fileName": "u.pdf"}] if path == "DU/1994/214" else [],
                    "references": {g: [{"id": i, "date": d} for i, d in items.items()] for g, items in old["references"].items()}}
            if new_amendment and path == "DU/1994/214":
                data["references"]["Akty zmieniające"].append({"id": "DU/2099/1", "date": "2100-01-01"})
            return data

        def digest(path):
            return "zmieniony" if new_text else baseline["acts"]["DU/1994/214"]["textHash"]
        return get, digest

    def run_check(self, **flags):
        get, digest = self.fake_api(**flags)
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            report = Path(folder) / "r.md"
            self.assertEqual(check_law.main(["x", "--report", str(report)], get=get, digest=digest, today=date(2026, 11, 1)), 0)
            return report.read_text(encoding="utf-8") if report.exists() else ""

    def test_new_amendment_is_reported_without_network(self):
        text = self.run_check(new_amendment=True)
        self.assertIn("DU/2099/1", text)
        self.assertIn("Ustawa testowa", text)

    def test_new_notice_is_reported(self):
        self.assertIn("MP/2099/7", self.run_check(new_notice=True))

    def test_changed_consolidated_text_is_reported(self):
        self.assertIn("tekst ujednolicony", self.run_check(new_text=True))

    def test_nothing_new_only_deadlines(self):
        text = self.run_check()
        self.assertIn("Terminy w kodzie", text)
        self.assertNotIn("Zmiany w obserwowanych aktach", text)
        self.assertNotIn("Nowe komunikaty", text)


if __name__ == "__main__":
    unittest.main()
