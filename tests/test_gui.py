"""Integracja własnych komponentów GUI. Włącz EMKA_GUI_TEST=1 w sesji graficznej."""
import copy
import os
import unittest
from unittest.mock import patch
from emka.engine import Extra, Bonus


@unittest.skipUnless(os.environ.get("EMKA_GUI_TEST") == "1", "Wymaga sesji graficznej i EMKA_GUI_TEST=1")
class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from emka.gui import App
        cls.app = App()
        cls.app.withdraw()
        cls.app.update()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        from emka.engine import Profile
        self.app.fill_profile(Profile())
        self.app.snapshots = []
        self.app.refresh_comparison()

    def test_disclaimer_always_visible_in_result_panel(self):
        from emka.helptext import DISCLAIMER
        self.assertEqual(self.app.disclaimer.cget("text"), DISCLAIMER)
        self.app.calculate_show()
        self.assertTrue(self.app.disclaimer.winfo_manager())

    def test_all_pages_created(self):
        self.assertEqual(len(self.app.notebook.tabs()), 8)
        self.assertEqual(len(self.app.forecast_tree.get_children()), 20)

    def test_dirty_state_clears_result(self):
        self.app.vars["base"].set("15000")
        self.assertIsNone(self.app.result)
        self.assertEqual(len(self.app.forecast_tree.get_children()), 0)
        self.assertTrue(self.app.calculate_show())
        self.assertEqual(self.app.result.basis, 15000)

    def test_snapshot_is_independent(self):
        self.app.add_snapshot()
        self.app.vars["base"].set("12000")
        self.app.calculate_show()
        self.assertEqual(self.app.snapshots[0].base, "10000")
        self.app.compare_tree.selection_set("0")
        self.app.restore_snapshot()
        self.assertEqual(self.app.vars["base"].get(), "10000")

    def test_invalid_input_no_stale_result(self):
        self.app.vars["base"].set("NaN")
        with patch("emka.gui.messagebox.showerror") as error:
            self.assertFalse(self.app.calculate_show())
            error.assert_called_once()
        self.assertIsNone(self.app.result)

    def test_nested_lists_and_deletion(self):
        p = copy.deepcopy(self.app.profile)
        p.extras = [Extra(value="2")]
        p.bonuses = [Bonus(confirmed=True)]
        p.overrides = {"2027": {"growth": "5", "inflation": "3"}}
        self.app.fill_profile(p)
        self.assertEqual(len(self.app.extra_tree.get_children()), 1)
        self.app.extra_tree.selection_set("0")
        self.app.delete_record("extras", self.app.extra_tree)
        self.assertEqual(len(self.app.profile.extras), 0)
        self.assertIsNone(self.app.result)

    def test_chart_for_single_year(self):
        self.app.vars["forecast_years"].set("1")
        self.assertTrue(self.app.calculate_show())
        self.app.draw_chart()
        self.assertGreater(len(self.app.chart.find_all()), 5)

    def test_system_checkbox_and_date_sync(self):
        self.app.vars["first_entry"].set("2013-01-01")
        self.assertTrue(self.app.vars["new_system"].get())
        self.assertIn("25 lat: 60%", self.app.rule_context.cget("text"))
        self.app.vars["first_entry"].set("2001-01-01")
        self.assertFalse(self.app.vars["new_system"].get())
        self.app.vars["new_system"].set(True)
        self.assertTrue(self.app.calculate_show())
        self.assertIn("18h", self.app.result.regime)

    def test_service_context_and_saved_scenario(self):
        self.app.vars["service"].set("PSP")
        self.assertIn("30 dni", self.app.rule_context.cget("text"))
        self.app.add_snapshot()
        self.app.vars["service"].set("SM")
        self.assertIn("10 kolejnych lat", self.app.rule_context.cget("text"))
        self.app.compare_tree.selection_set("0")
        self.app.show_snapshot_rules()
        self.assertIn("Państwowa Straż Pożarna", self.app.compare_rules.cget("text"))

    def test_service_list_shows_full_names_but_stores_abbreviation(self):
        self.app.vars["service"].set("SM")
        displayed = [w for w in self._all_widgets(self.app) if hasattr(w, "display_var")]
        self.assertEqual(displayed[0].display_var.get(), "SM — Straż Marszałkowska")
        displayed[0].set("SG — Straż Graniczna")
        displayed[0].event_generate("<<ComboboxSelected>>")
        self.assertEqual(self.app.vars["service"].get(), "SG")

    def _all_widgets(self, widget):
        found = [widget]
        for child in widget.winfo_children():
            found += self._all_widgets(child)
        return found

    def test_tcl_special_characters_in_names_stay_plain_text(self):
        """Nazwy z nawiasami, dolarem i cudzysłowem nie mogą być wykonane jako polecenia Tcl."""
        from emka.engine import Profile
        name = '[exit] {x} $y \\ "q" ;set a b'
        self.app.fill_profile(Profile(extras=[Extra(name=name, value="1")]))
        self.app.refresh_tables()
        self.assertEqual(self.app.extra_tree.item("0", "values")[0], name)
        self.assertTrue(self.app.winfo_exists())

    def test_months_hint_follows_dates(self):
        self.app.vars["first_entry"].set("01.01.2001")
        self.app.vars["release"].set("2026-10-31")
        self.assertIn("310 mies.", self.app.months_hint.cget("text"))
        self.app.vars["release"].set("nie data")
        self.assertEqual(self.app.months_hint.cget("text"), "")

    def test_error_message_uses_polish_field_name(self):
        self.app.vars["service_months"].set("abc")
        with patch("emka.gui.messagebox.showerror") as error:
            self.assertFalse(self.app.calculate_show())
        self.assertIn("Łączna wysługa", error.call_args.args[1])

    def test_net_and_earnings_shown(self):
        self.assertIn("Netto:", self.app.net_label.cget("text"))
        self.assertEqual(self.app.work_label.cget("text"), "")
        self.assertEqual(len(self.app.earn_tree.get_children()), 4)
        self.app.vars["work_income"].set("9000")  # zmiana unieważnia wynik
        self.assertEqual(self.app.net_label.cget("text"), "")
        self.assertTrue(self.app.calculate_show())
        self.assertIn("989,41", self.app.work_label.cget("text"))
        self.assertIn("zmniejszona o", self.app.earn_summary.cget("text"))

    def test_law_tab_renders_markdown(self):
        text = self.app.law_text.get("1.0", "end")
        self.assertIn("EMKA: analiza przepisów", text)
        for raw in ("**", "## ", "](http"):
            self.assertNotIn(raw, text)
        self.assertTrue(self.app.law_text.tag_ranges("link"))
        self.assertTrue(self.app.law_text.tag_ranges("h2"))

    def test_forecast_headings_have_descriptions(self):
        from emka.helptext import FORECAST_COLUMNS
        headings = [self.app.forecast_tree.heading(c, "text") for c in self.app.forecast_tree["columns"]]
        self.assertEqual(headings, [name for name, _ in FORECAST_COLUMNS])
        help_ = self.app.forecast_help
        self.assertIn("ceny", help_.column_text("#5"))  # Wartość realna
        self.assertEqual(help_.column_text("#0"), "")
        self.assertEqual(help_.column_text(""), "")
        self.assertEqual(help_.column_text("#99"), "")
        help_.show_at(help_.column_text("#3"), 100, 100, 100)
        self.assertIsNotNone(help_.window)
        help_.hide()
        self.assertIsNone(help_.window)

    def test_earnings_headings_have_descriptions(self):
        self.assertIn("składki zdrowotnej", self.app.earn_help.column_text("#4"))

    def test_chart_lines_can_be_toggled(self):
        self.app.update()
        items_default = len(self.app.chart.find_all())
        for variable in self.app.chart_vars.values():
            variable.set(False)
        self.assertLess(len(self.app.chart.find_all()), items_default)  # tylko komunikat
        self.assertTrue(any("Zaznacz" in str(self.app.chart.itemcget(i, "text"))
                            for i in self.app.chart.find_all() if self.app.chart.type(i) == "text"))
        self.app.chart_vars["net_december"].set(True)
        self.assertGreater(len(self.app.chart.find_all()), 5)
        # Zmiana wykresu nie unieważnia wyniku (to nie dane profilu).
        self.assertIsNotNone(self.app.result)

    def test_icon_is_loaded(self):
        from emka.gui import ICON_PATH
        self.assertTrue(ICON_PATH.exists())
        self.assertGreater(self.app.icon.width(), 100)

    def test_tooltip_constructs_and_closes(self):
        from emka.gui import Tooltip
        tip = Tooltip(self.app.amount, "Treść pomocy")
        tip.show()
        self.assertIsNotNone(tip.window)
        self.app.update_idletasks()
        tip.hide()
        self.assertIsNone(tip.window)

    def test_editors_construct(self):
        from emka.gui import Editor
        self.app.edit_pay()
        self.app.update_idletasks()
        editors = [w for w in self.app.winfo_children() if isinstance(w, Editor)]
        self.assertEqual(len(editors), 1)
        editors[0].destroy()
        self.app.edit_extra()
        self.app.update_idletasks()
        editors = [w for w in self.app.winfo_children() if isinstance(w, Editor)]
        self.assertEqual(len(editors), 1)
        editors[0].destroy()


if __name__ == "__main__":
    unittest.main()
