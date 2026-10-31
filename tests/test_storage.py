import json
import tempfile
import unittest
from pathlib import Path
from emka import __version__
from emka.engine import Profile, Bonus, Extra, calculate
from emka.helptext import DISCLAIMER
from emka.storage import MAX_PROFILE_BYTES, decode_profile, save_profile, load_profile, export_csv, report


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


class HostileInputTests(unittest.TestCase):
    """Plik profilu może pochodzić od kogoś innego, więc traktujemy go jak dane niezaufane (STRIDE: T, D, I)."""

    def decode(self, **changes):
        from dataclasses import asdict
        data = asdict(Profile())
        data.update(changes)
        return decode_profile(data)

    def test_names_must_be_short_plain_text(self):
        for bad in (["x"], 5, "A" * 101, "linia\nnowa", "tab\tulator", "\x00"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.decode(name=bad)
        self.assertEqual(self.decode(name="Ąęść – próba").name, "Ąęść – próba")

    def test_nested_record_names_are_checked_too(self):
        with self.assertRaises(ValueError):
            self.decode(extras=[{"name": "a\nb", "unit": "zł miesięcznie", "value": "1", "indexed": True, "enabled": True}])
        with self.assertRaises(ValueError):
            self.decode(bonuses=[{"name": 7, "kind": "0,5%/rok", "start": "2005-01", "end": "2005-12", "confirmed": False}])

    def test_wrong_record_fields_give_value_error_not_type_error(self):
        with self.assertRaises(ValueError):
            self.decode(bonuses=[{"nope": 1}])

    def test_extreme_numbers_are_rejected_quickly(self):
        for changes in ({"base": "1e999999"}, {"base": "Infinity"}, {"base": "NaN"}, {"growth": "1e500"},
                        {"service_months": 10 ** 30}, {"forecast_years": 10 ** 9}, {"release": "9999-12-31", "right_date": "9999-12-31"}):
            with self.assertRaises(ValueError, msg=str(changes)):
                self.decode(**changes)

    def test_oversized_file_is_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "big.json"
            path.write_bytes(b" " * (MAX_PROFILE_BYTES + 1))
            with self.assertRaises(ValueError):
                load_profile(path)

    def test_csv_contains_only_numbers_so_no_spreadsheet_formulas(self):
        p = Profile(name="=HYPERLINK(\"http://zly.example\")", extras=[Extra(name="+cmd|calc")])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "forecast.csv"
            export_csv(path, p, calculate(p))
            body = path.read_text(encoding="utf-8-sig")
        self.assertNotIn("HYPERLINK", body)
        self.assertNotIn("cmd", body)
        for line in body.splitlines()[1:]:
            for cell in line.split(";"):
                self.assertRegex(cell, r"^-?[0-9]+(,[0-9]+)?$")

    def test_report_name_cannot_inject_headings(self):
        p = Profile(name="Zwykła")
        p.name = "Jan\n## Fałszywy nagłówek"  # obejście walidacji, jakby ktoś ustawił nazwę z kodu
        text = report(p, calculate(p))
        self.assertEqual(text.splitlines()[0], "# EMKA — Jan ## Fałszywy nagłówek")
        self.assertNotIn("\n## Fałszywy nagłówek", text)

    def test_failed_save_leaves_old_file_and_no_temporary_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "profile.json"
            save_profile(path, Profile(name="stary"))
            bad_target = Path(d) / "brak-katalogu" / "x.json"
            with self.assertRaises(OSError):
                save_profile(bad_target, Profile())
            self.assertEqual(load_profile(path).name, "stary")
            self.assertEqual(sorted(f.name for f in Path(d).iterdir()), ["profile.json"])

    def test_saved_file_records_program_version(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "profile.json"
            save_profile(path, Profile())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["app_version"], __version__)
        self.assertIn(f"Wersja programu: {__version__}", report(Profile(), calculate(Profile())))


class ShippedFilesTests(unittest.TestCase):
    """Profile przykładowe z katalogu examples/ muszą się wczytywać i liczyć."""

    ROOT = Path(__file__).resolve().parent.parent

    def test_disclaimer_is_in_report_readme_and_law_text(self):
        self.assertIn("nie oficjalny kalkulator", DISCLAIMER)
        self.assertIn(DISCLAIMER, report(Profile(), calculate(Profile())))
        for relative in ("README.md", "emka/PRZEPISY.md"):
            text = (self.ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("narzędziem poglądowym" if "PRZEPISY" in relative else "narzędzie poglądowe", text, relative)
            self.assertIn("nie oficjalny" if "README" in relative else "nie oficjalnym", text, relative)
        self.assertIn("Poglądowy", (self.ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    def test_example_profiles_load(self):
        examples = Path(__file__).resolve().parent.parent / "examples"
        profiles = sorted(examples.glob("*.json"))
        self.assertTrue(profiles)
        for path in profiles:
            calculate(load_profile(path))


if __name__ == "__main__":
    unittest.main()
