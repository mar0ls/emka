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
