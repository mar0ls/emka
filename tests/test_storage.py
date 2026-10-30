import json
import tempfile
import unittest
from pathlib import Path
from emka.engine import Profile, Bonus, Extra, calculate
from emka.storage import save_profile, load_profile, export_csv, report


class StorageTests(unittest.TestCase):
    def test_round_trip_all_nested_records(self):
        p = Profile(bonuses=[Bonus(confirmed=True)], extras=[Extra(value="2")], overrides={"2027": {"growth": "5", "inflation": "3"}})
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"profile.json"
            save_profile(path, p)
            self.assertEqual(load_profile(path), p)

    def test_unknown_version_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"profile.json"
            path.write_text('{"schema_version": 999, "profile": {}}')
            with self.assertRaises(ValueError):
                load_profile(path)

    def test_malformed_and_wrong_types_rejected(self):
        for profile in ({"service_months": "NaN"}, {"medal": "false"}, {"unknown": 42}, {"extras": [{"enabled": "false"}]}, {"annual_pay": ["invalid"]}):
            with tempfile.TemporaryDirectory() as d:
                path = Path(d)/"profile.json"
                path.write_text(json.dumps({"schema_version": 1, "profile": profile}))
                with self.assertRaises(ValueError):
                    load_profile(path)

    def test_csv_and_report(self):
        p = Profile()
        r = calculate(p)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"forecast.csv"
            export_csv(path, p, r)
            self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))
            lines = path.read_text(encoding="utf-8-sig").splitlines()
            self.assertEqual(len(lines), 21)
            self.assertIn("Netto (mies.)", lines[0])
        document = report(p, r)
        self.assertIn("6816.67", document)
        self.assertIn("Pełna konfiguracja", document)
        self.assertIn("## Emerytura netto", document)
        self.assertIn("## Dorabianie w cywilnej firmie", document)
        self.assertIn("eli.gov.pl", document)
        self.assertIn("**Wartość realna** —", document)


if __name__ == "__main__":
    unittest.main()
