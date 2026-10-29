import unittest
from dataclasses import replace
from decimal import Decimal as D
from emka.engine import (Profile, Bonus, Extra, AnnualPay, calculate, earnings_effect, earnings_table, forecast,
                         full_months_between, net_pension, number, parse_date, reduction_for, select_regime,
                         service_rules)
from datetime import date


class PensionTests(unittest.TestCase):
    def profile(self, **kwargs):
        return replace(Profile(), first_entry="1990-01-01", service_months=180, qualifying_25_months=180, **kwargs)

    def test_fifteen_years(self):
        r = calculate(self.profile())
        self.assertEqual(r.pension, D("4000.00"))
        self.assertTrue(r.eligible)

    def test_no_entitlement_one_month_short(self):
        p = self.profile()
        p.service_months = p.qualifying_25_months = 179
        p.extras = [Extra(value="1500", unit="zł miesięcznie")]
        r = calculate(p)
        self.assertFalse(r.eligible)
        self.assertEqual(r.missing_months, 1)
        self.assertEqual(r.scenario, 0)
        self.assertEqual(forecast(p, r), [])

    def test_one_month_growth(self):
        p = self.profile()
        p.service_months = 181
        self.assertEqual(calculate(p).pension, D("4021.67"))

    def test_civil_pre_service(self):
        p = self.profile(pre_contrib_months=60, pre_noncontrib_months=12)
        self.assertEqual(calculate(p).pension, D("5110.00"))

    def test_civil_ignored_15a(self):
        p = replace(Profile(), pre_contrib_months=60, pre_noncontrib_months=12)
        self.assertEqual(calculate(p).pension, calculate(Profile()).pension)

    def test_boundary_dates(self):
        for value, expected in (("1999-01-01", "15"), ("1999-01-02", "15a"), ("2012-12-31", "15a"), ("2013-01-01", "18e")):
            with self.subTest(value=value):
                self.assertEqual(select_regime(replace(Profile(), first_entry=value)), expected)

    def test_explicit_system_checkbox(self):
        self.assertEqual(select_regime(replace(Profile(), new_system=True)), "18h → 18e")
        self.assertEqual(select_regime(replace(Profile(), new_system=False)), "15a")
        self.assertEqual(select_regime(replace(Profile(), first_entry="2013-01-01", new_system=True)), "18e")
        with self.assertRaises(ValueError):
            select_regime(replace(Profile(), first_entry="2013-01-01", new_system=False))
        with self.assertRaises(ValueError):
            select_regime(replace(Profile(), regime="15aa", new_system=True))

    def test_service_specific_legal_context(self):
        for s in ("SM", "SC", "SCS"):
            self.assertIn("10 kolejnych lat", service_rules(replace(Profile(), service=s)))
        self.assertIn("wojskowy organ", service_rules(replace(Profile(), service="SKW")))
        self.assertIn("Ministra Sprawiedliwości", service_rules(replace(Profile(), service="SW")))
        self.assertIn("30 dni", service_rules(replace(Profile(), service="PSP")))
        self.assertIn("25 lat: 60%", service_rules(replace(Profile(), new_system=True)))

    def test_15aa_both_boundaries(self):
        for value in ("1999-01-02", "2003-09-30"):
            self.assertEqual(select_regime(replace(Profile(), first_entry=value, regime="15aa")), "15aa")
        for value in ("1999-01-01", "2003-10-01", "2013-01-01"):
            with self.assertRaises(ValueError):
                select_regime(replace(Profile(), first_entry=value, regime="15aa"))

    def test_15aa_requires_specific_25_years(self):
        p = replace(Profile(), regime="15aa", pre_contrib_months=12, service_months=300, qualifying_25_months=299)
        before = calculate(p).pension
        p.qualifying_25_months = 300
        self.assertEqual(calculate(p).pension-before, 130)

    def test_modern_25_years(self):
        p = replace(Profile(), first_entry="2013-01-01", release="2037-12-31", right_date="2038-01-01", service_months=300, qualifying_25_months=300)
        self.assertEqual(calculate(p).pension, 6000)
        p.service_months = 301
        p.release, p.right_date = "2038-01-31", "2038-02-01"
        self.assertEqual(calculate(p).pension, 6025)

    def test_modern_no_55_year_age_requirement(self):
        p = replace(Profile(), first_entry="2013-01-01", release="2037-12-31", right_date="2038-01-01", service_months=300, qualifying_25_months=300)
        self.assertTrue(calculate(p).eligible)

    def test_optional_modern(self):
        p = replace(Profile(), regime="18h", service_months=300, qualifying_25_months=300)
        self.assertEqual(calculate(p).pension, 6000)

    def test_all_caps(self):
        for disability, medal, cap in ((False, False, 75), (True, False, 80), (False, True, 76), (True, True, 81)):
            p = self.profile(disability=disability, medal=medal)
            p.service_months = 420
            r = calculate(p)
            self.assertEqual(r.cap, cap)
            self.assertEqual(r.pension, D(cap)*100)

    def test_modern_cap_and_medal(self):
        p = replace(Profile(), first_entry="2013-01-01", release="2047-12-31", right_date="2048-01-01", service_months=420, qualifying_25_months=420, medal=True)
        self.assertEqual(calculate(p).pension, 7600)
        p.disability = True
        with self.assertRaises(ValueError):
            calculate(p)

    def test_bonus_overlap_only_highest(self):
        p = self.profile(bonuses=[Bonus(kind="2%/rok", confirmed=True), Bonus(kind="1%/rok", confirmed=True)])
        r = calculate(p)
        self.assertEqual(r.pension, 4200)
        self.assertTrue(any("Nakładające" in s for s in r.warnings))

    def test_bonuses_non_overlapping(self):
        p = self.profile(bonuses=[Bonus(kind="2%/rok", confirmed=True), Bonus(kind="1%/rok", start="2006-01", end="2006-12", confirmed=True)])
        self.assertEqual(calculate(p).pension, 4300)

    def test_war_started_month(self):
        p = self.profile(bonuses=[Bonus(kind="strefa wojny", start="2005-01", end="2005-01", confirmed=True)])
        self.assertEqual(calculate(p).pension, 4050)

    def test_unconfirmed_bonus_blocked(self):
        with self.assertRaises(ValueError):
            calculate(self.profile(bonuses=[Bonus()]))

    def test_outside_bonus_blocked(self):
        with self.assertRaises(ValueError):
            calculate(self.profile(bonuses=[Bonus(start="1989-01", confirmed=True)]))

    def test_modern_annual_bonus_blocked(self):
        with self.assertRaises(ValueError):
            calculate(replace(Profile(), regime="18h", bonuses=[Bonus(confirmed=True)]))

    def test_special_cases_blocked(self):
        for key in ("special_case", "exclusion", "fus_service_used"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                calculate(replace(Profile(), **{key: True}))

    def test_old_post_civil_requires_conditions(self):
        p = self.profile(post_contrib_months=12)
        with self.assertRaises(ValueError):
            calculate(p)
        p.post_conditions = True
        self.assertEqual(calculate(p).pension, 4130)

    def test_15aa_post_no_age_in_engine(self):
        p = replace(Profile(), regime="15aa", service_months=300, qualifying_25_months=300, post_contrib_months=12, post_conditions=True)
        self.assertEqual(calculate(p).pension, 6730)

    def test_15a_post_blocked(self):
        with self.assertRaises(ValueError):
            calculate(replace(Profile(), post_contrib_months=12, post_conditions=True))

    def test_old_minimum(self):
        self.assertEqual(calculate(self.profile(base="1000")).pension, D("1978.49"))

    def test_fus_minimum_complement(self):
        p = replace(Profile(), service_months=180, qualifying_25_months=180, base="1000", fus_pension="1000")
        self.assertEqual(calculate(p).pension, D("978.49"))

    def test_ready_basis_no_double_addition(self):
        p = self.profile(longevity="1000")
        p.service_months = 420
        self.assertEqual(calculate(p).basis, 10000)

    def test_salary_components(self):
        p = self.profile(base_mode="składniki uposażenia", salary="8000", permanent="1000", annual_award="12000")
        self.assertEqual(calculate(p).basis, 10000)

    def test_longevity_requires_32_years(self):
        with self.assertRaises(ValueError):
            calculate(self.profile(base_mode="składniki uposażenia", longevity="1000"))

    def test_ten_year_ratio_not_average(self):
        p = replace(Profile(), regime="18h", base_mode="10 kolejnych lat", current_reference="10000")
        p.annual_pay = [AnnualPay(year=y, pay="120000" if y%2 else "200000", reference="100000" if y%2 else "200000") for y in range(2016, 2026)]
        self.assertEqual(calculate(p).basis, 11000)

    def test_ten_year_rounding_annual_ratio(self):
        p = replace(Profile(), regime="18h", base_mode="10 kolejnych lat", current_reference="10000")
        p.annual_pay = [AnnualPay(year=y, pay="100004", reference="100000") for y in range(2016, 2026)]
        self.assertEqual(calculate(p).basis, 10000)

    def test_ten_year_consecutive_required(self):
        p = replace(Profile(), regime="18h", base_mode="10 kolejnych lat")
        p.annual_pay = [AnnualPay(year=2016) for _ in range(10)]
        with self.assertRaises(ValueError):
            calculate(p)

    def test_customs_and_marshal_basis(self):
        for service in ("SC", "SCS", "SM"):
            p = replace(Profile(), service=service, base_mode="składniki uposażenia")
            with self.assertRaises(ValueError):
                calculate(p)

    def test_customs_regimes(self):
        self.assertEqual(select_regime(replace(Profile(), service="SCS")), "15d → 15a")
        self.assertEqual(select_regime(replace(Profile(), service="SCS", first_entry="1990-01-01")), "15e → 15")

    def test_custom_extras_separate_from_cap(self):
        p = self.profile(extras=[Extra(value="2"), Extra(unit="% emerytury", value="10"), Extra(unit="zł miesięcznie", value="100", indexed=False)])
        r = calculate(p)
        self.assertEqual(r.pension, 4000)
        self.assertEqual(r.scenario, 4700)
        self.assertEqual(r.fixed_extra, 100)

    def test_disabled_extra(self):
        r = calculate(self.profile(extras=[Extra(value="50", enabled=False)]))
        self.assertEqual(r.scenario, r.pension)

    def test_reject_nonfinite_and_negative(self):
        for value in ("NaN", "Infinity", "-1", "wrong"):
            with self.assertRaises(ValueError):
                number(value)
        self.assertEqual(number("1 234,56"), D("1234.56"))

    def test_impossible_service_and_qualifying(self):
        for p in (replace(Profile(), service_months=1000), replace(Profile(), qualifying_25_months=311)):
            with self.assertRaises(ValueError):
                calculate(p)

    def test_historical_release_blocked(self):
        with self.assertRaises(ValueError):
            calculate(replace(Profile(), release="2025-01-01"))

    def test_service_months_checked_against_exact_dates(self):
        # 15.01.2001 - 31.10.2026 to 309 pełnych miesięcy, nie 310.
        p = replace(Profile(), first_entry="2001-01-15")
        with self.assertRaises(ValueError):
            calculate(p)
        p.service_months = p.qualifying_25_months = 309
        self.assertTrue(calculate(p).eligible)

    def test_full_months_between(self):
        self.assertEqual(full_months_between(date(2001, 1, 1), date(2026, 10, 31)), 310)
        self.assertEqual(full_months_between(date(2001, 1, 15), date(2026, 10, 31)), 309)
        self.assertEqual(full_months_between(date(2020, 1, 1), date(2020, 1, 31)), 1)
        self.assertEqual(full_months_between(date(2020, 1, 1), date(2020, 1, 30)), 0)

    def test_polish_date_formats(self):
        self.assertEqual(parse_date("31.10.2026", "x"), date(2026, 10, 31))
        self.assertEqual(parse_date("2026-10-31", "x"), date(2026, 10, 31))
        with self.assertRaises(ValueError):
            parse_date("31/10/2026", "x")
        p = replace(Profile(), first_entry="01.01.2001", release="31.10.2026", right_date="01.11.2026",
                    bonuses=[Bonus(kind="strefa wojny", start="01.2005", end="01.2005", confirmed=True)])
        self.assertEqual(calculate(p).pension, D("6866.67"))

    def test_longevity_ignored_with_ready_basis(self):
        # W trybie gotowej podstawy pole świadczenia nie jest używane, więc nie może blokować obliczeń.
        self.assertTrue(calculate(self.profile(longevity="500")).eligible)

    def test_calculate_does_not_change_profile(self):
        p = self.profile()
        p.service_months = "180"
        calculate(p)
        self.assertEqual(p.service_months, "180")

    def test_error_names_field_in_polish(self):
        p = self.profile()
        p.service_months = "abc"
        with self.assertRaisesRegex(ValueError, "Łączna wysługa"):
            calculate(p)

    def test_unknown_base_mode_rejected(self):
        with self.assertRaises(ValueError):
            calculate(self.profile(base_mode="losowo"))


class NetTests(unittest.TestCase):
    def test_minimum_pension_pays_no_tax(self):
        net = net_pension(D("1978.49"))
        self.assertEqual((net.health, net.tax, net.net), (D("178.06"), 0, D("1800.43")))

    def test_tax_with_and_without_tax_reducing_amount(self):
        self.assertEqual(net_pension(D("7000")).tax, 540)  # 12% * 7000 - 300
        self.assertEqual(net_pension(D("7000"), False).tax, 840)
        self.assertEqual(net_pension(D("10000")).net, D("8200.00"))

    def test_second_tax_bracket_above_120k_a_year(self):
        # 11 000 zł * 12 = 132 000 zł: 10 800 zł + 32% * 12 000 zł = 14 640 zł rocznie = 1 220 zł miesięcznie.
        net = net_pension(D("11000"))
        self.assertEqual((net.tax, net.health, net.net), (1220, D("990.00"), D("8790.00")))

    def test_forecast_contains_net(self):
        p = replace(Profile(), release="2026-12-31", right_date="2027-01-01", forecast_years=1)
        row = forecast(p, calculate(p))[0]
        self.assertEqual(row.net_december, net_pension(row.december).net)


class EarningsTests(unittest.TestCase):
    LOW, HIGH, MAX = D("6463.20"), D("12003.10"), D("989.41")

    def reduction(self, income, pension=D("6816.67"), exempt=False):
        return reduction_for(D(income), pension, self.LOW, self.HIGH, self.MAX, exempt)

    def test_no_reduction_up_to_70_percent(self):
        self.assertEqual(self.reduction("6463.20"), ("below", 0))
        self.assertEqual(self.reduction("0"), ("below", 0))

    def test_reduction_equals_excess_over_70_percent(self):
        self.assertEqual(self.reduction("6700"), ("reduced", D("236.80")))

    def test_reduction_limited_by_maximum_amount(self):
        self.assertEqual(self.reduction("9000"), ("reduced", D("989.41")))
        self.assertEqual(self.reduction("12003.10"), ("reduced", D("989.41")))

    def test_reduction_limited_to_25_percent_of_small_pension(self):
        self.assertEqual(self.reduction("9000", pension=D("2000")), ("reduced", D("500.00")))

    def test_over_130_percent_cuts_exactly_25_percent_not_suspension(self):
        self.assertEqual(self.reduction("12003.11"), ("over", D("1704.17")))
        self.assertEqual(self.reduction("50000", pension=D("4000")), ("over", D("1000.00")))

    def test_exempt_pension_is_never_reduced(self):
        self.assertEqual(self.reduction("50000", exempt=True), ("below", 0))

    def test_effect_for_profile(self):
        p = replace(Profile(), work_income="9000")
        effect = earnings_effect(p, calculate(p))
        self.assertEqual((effect.zone, effect.reduction, effect.pension_after), ("reduced", D("989.41"), D("5827.26")))
        self.assertLess(effect.net_after.net, effect.net_before.net)
        self.assertFalse(effect.exempt)

    def test_75_percent_pension_is_exempt_but_75_with_disability_bonus_counts_without_it(self):
        full = replace(Profile(), first_entry="1990-01-01", service_months=420, qualifying_25_months=420,
                       work_income="20000")
        self.assertTrue(earnings_effect(full, calculate(full)).exempt)
        self.assertEqual(earnings_effect(full, calculate(full)).reduction, 0)
        # Art. 41 ust. 4: +15 pp za inwalidztwo nie liczy się do progu 75%.
        short = replace(full, service_months=180, qualifying_25_months=180, disability=True)
        effect = earnings_effect(short, calculate(short))
        self.assertFalse(effect.exempt)
        self.assertGreater(effect.reduction, 0)

    def test_warns_about_jump_at_130_percent(self):
        p = replace(Profile(), work_income="9000")
        text = " ".join(earnings_effect(p, calculate(p)).warnings)
        self.assertIn("989.41", text)
        self.assertIn("1704.17", text)
        # Przy emeryturze 75% podstawy (zwolnionej ze zmniejszeń) ostrzeżenia nie ma.
        full = replace(p, first_entry="1990-01-01", service_months=420, qualifying_25_months=420)
        self.assertNotIn("130%", " ".join(earnings_effect(full, calculate(full)).warnings))

    def test_no_effect_without_entitlement(self):
        p = replace(Profile(), service_months=100, qualifying_25_months=100, work_income="9000")
        self.assertIsNone(earnings_effect(p, calculate(p)))

    def test_invalid_limits_rejected(self):
        p = replace(Profile(), income_limit_low="9000", income_limit_high="8000")
        with self.assertRaises(ValueError):
            earnings_effect(p, calculate(p))

    def test_table_is_monotonic(self):
        p = Profile()
        rows = earnings_table(p, calculate(p))
        reductions = [row[1] for row in rows]
        self.assertEqual(reductions, sorted(reductions))
        self.assertEqual(reductions[0], 0)


class ForecastTests(unittest.TestCase):
    def p(self, **kwargs):
        return replace(Profile(), release="2026-12-31", right_date="2027-01-01", growth="10", inflation="0", forecast_years=2, **kwargs)

    def test_march_cashflow(self):
        p = self.p()
        r = calculate(p)
        rows = forecast(p, r)
        self.assertEqual(rows[0].annual, r.pension*2 + rows[0].december*10)
        self.assertEqual(rows[0].december, (r.pension*D("1.1")).quantize(D("0.01")))
        self.assertEqual(rows[1].cumulative, rows[0].annual+rows[1].annual)

    def test_right_on_march_skips_first(self):
        p = self.p()
        p.release, p.right_date = "2027-02-28", "2027-03-01"
        rows = forecast(p, calculate(p))
        self.assertEqual(rows[0].rate, 0)
        self.assertEqual(rows[1].rate, 10)
        self.assertEqual(rows[0].annual, rows[0].december*10)

    def test_right_before_march_indexes(self):
        p = self.p()
        p.release, p.right_date = "2027-01-31", "2027-02-28"
        rows = forecast(p, calculate(p))
        self.assertEqual(rows[0].rate, 10)
        self.assertEqual(rows[0].annual, rows[0].before_march+10*rows[0].december)

    def test_late_release_two_months(self):
        p = Profile()
        row = forecast(p, calculate(p))[0]
        self.assertEqual(row.annual, row.december*2)

    def test_nonindexed_extra_constant(self):
        p = self.p(extras=[Extra(unit="zł miesięcznie", value="100", indexed=False)])
        rows = forecast(p, calculate(p))
        for row in rows:
            self.assertEqual(row.december-row.legal_december, 100)

    def test_overrides_and_inflation(self):
        p = self.p(overrides={"2027": {"growth": "0", "inflation": "10"}})
        rows = forecast(p, calculate(p))
        self.assertEqual(rows[0].rate, 0)
        self.assertEqual(rows[0].real_december, (rows[0].december/D("1.1")).quantize(D("0.01")))
        self.assertEqual(rows[1].rate, 10)

    def test_negative_growth_rejected(self):
        p = self.p()
        p.growth = "-1"
        with self.assertRaises(ValueError):
            forecast(p, calculate(p))

    def test_out_of_horizon_override_rejected(self):
        p = self.p(overrides={"2035": {"growth": "4", "inflation": "2"}})
        with self.assertRaises(ValueError):
            forecast(p, calculate(p))


if __name__ == "__main__":
    unittest.main()
