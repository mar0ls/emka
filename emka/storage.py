"""Zapis i odczyt profili JSON oraz eksport do CSV i raportu Markdown.

Pliki są tylko czytane jako dane - nigdy nie uruchamiamy ich zawartości.
"""
import csv
import json
from dataclasses import asdict, fields
from pathlib import Path

from .engine import (AnnualPay, Bonus, Extra, Profile, RULE_DATE, calculate, earnings_effect, earnings_table,
                     forecast, net_pension, service_rules)

SCHEMA_VERSION = 1
MAX_PROFILE_BYTES = 2_000_000
MAX_LIST_ITEMS = 1000
MAX_OVERRIDES = 60

# Pola, które w JSON muszą być prawdziwymi wartościami true/false (a nie napisem "false").
BOOLEAN_FIELDS = ("post_conditions", "disability", "medal", "special_case", "fus_service_used", "exclusion", "pit2")


def _require_bool(value, message):
    if type(value) is not bool:
        raise ValueError(message)


def decode_profile(data):
    """Buduje `Profile` ze słownika i od razu sprawdza, czy da się go obliczyć."""
    known_fields = {f.name for f in fields(Profile)}
    if not isinstance(data, dict) or set(data) - known_fields:
        raise ValueError("Niepoprawne lub nieznane pola profilu.")

    data = dict(data)
    for key, record_class in (("annual_pay", AnnualPay), ("bonuses", Bonus), ("extras", Extra)):
        items = data.get(key, [])
        if not isinstance(items, list) or len(items) > MAX_LIST_ITEMS:
            raise ValueError(f"Niepoprawna lista: {key}.")
        data[key] = [record_class(**item) for item in items]

    profile = Profile(**data)
    for key in BOOLEAN_FIELDS:
        _require_bool(getattr(profile, key), f"{key}: wymagane true/false.")
    if profile.new_system is not None:
        _require_bool(profile.new_system, "new_system: wymagane true/false albo null (dobór automatyczny).")
    for bonus in profile.bonuses:
        _require_bool(bonus.confirmed, "Potwierdzenie podwyższenia musi być wartością true/false.")
    for extra in profile.extras:
        _require_bool(extra.indexed, "Stan własnego dodatku musi być wartością true/false.")
        _require_bool(extra.enabled, "Stan własnego dodatku musi być wartością true/false.")
    if not isinstance(profile.overrides, dict) or len(profile.overrides) > MAX_OVERRIDES:
        raise ValueError("Niepoprawne zmiany roczne.")

    # Profil, którego nie da się policzyć, nie powinien trafić do pliku ani do programu.
    forecast(profile, calculate(profile))
    return profile


def save_profile(path, profile):
    decode_profile(asdict(profile))  # walidacja przed zapisem
    path = Path(path)
    document = {"schema_version": SCHEMA_VERSION, "rules_checked": RULE_DATE, "profile": asdict(profile)}

    # Zapis przez plik tymczasowy: awaria w trakcie nie zniszczy poprzedniej wersji.
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def load_profile(path):
    path = Path(path)
    if path.stat().st_size > MAX_PROFILE_BYTES:
        raise ValueError("Plik profilu jest za duży (limit 2 MB).")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Nieobsługiwana wersja profilu.")
        return decode_profile(data["profile"])
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Nieprawidłowy profil JSON: {exc}") from None


def _polish_number(value):
    """Liczba z przecinkiem dziesiętnym - Excel w polskiej wersji otworzy ją bez problemu."""
    return str(value).replace(".", ",")


def export_csv(path, profile, result):
    """Zapisuje symulację do CSV (separator `;`, UTF-8 z BOM - tak otwiera go polski Excel)."""
    header = ("Rok", "Wzrost %", "Inflacja %", "Przed marcową waloryzacją brutto",
              "Grudzień brutto wariantu", "Grudzień z reguł ustawy", "Grudzień realnie",
              "Grudzień netto", "Wypłaty roczne brutto", "Suma brutto")
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(header)
        for row in forecast(profile, result):
            writer.writerow(_polish_number(value) for value in (
                row.year, row.rate, row.inflation, row.before_march, row.december,
                row.legal_december, row.real_december, row.net_december, row.annual, row.cumulative))


def _net_and_earnings_section(p, r):
    """Fragment raportu: emerytura netto oraz skutek dorabiania."""
    if not r.eligible:
        return []
    net = net_pension(r.pension, p.pit2)
    lines = ["", "## Emerytura netto", "",
             f"- Brutto: {net.gross:.2f} zł; składka zdrowotna 9%: {net.health:.2f} zł; "
             f"zaliczka na PIT: {net.tax:.2f} zł "
             f"({'z kwotą zmniejszającą 300 zł miesięcznie' if p.pit2 else 'bez kwoty zmniejszającej'}).",
             f"- **Netto: {net.net:.2f} zł/mies.**"]

    effect = earnings_effect(p, r)
    lines += ["", "## Dorabianie w cywilnej firmie", "",
              f"- Progi przychodu: 70% = {effect.low:.2f} zł, 130% = {effect.high:.2f} zł; "
              f"maksymalne zmniejszenie w strefie 70–130%: {p.max_reduction} zł; w każdym przypadku najwyżej 25% emerytury.",
              f"- Przychód brutto z pracy: {effect.income:.2f} zł/mies. → zmniejszenie emerytury o "
              f"**{effect.reduction:.2f} zł** (emerytura {effect.pension_after:.2f} zł brutto, "
              f"{effect.net_after.net:.2f} zł netto).",
              "", "| Przychód z pracy | Zmniejszenie | Emerytura brutto | Emerytura netto |", "|---|---|---|---|"]
    for income, reduction, after, net_after in earnings_table(p, r):
        lines.append(f"| {income:.2f} | {reduction:.2f} | {after:.2f} | {net_after:.2f} |")
    lines += [""] + [f"- {warning}" for warning in effect.warnings]
    return lines


def report(p, r):
    """Raport Markdown: wynik, założenia, tabela waloryzacji i pełna konfiguracja."""
    staz = "spełniony" if r.eligible else f"brakuje {r.missing_months} miesięcy"
    lines = [
        f"# EMKA — {p.name}", "",
        f"Reguły sprawdzone: {RULE_DATE}. Kwoty brutto; wynik orientacyjny.", "",
        f"Służba: {p.service}; pierwsze przyjęcie: {p.first_entry}; zwolnienie: {p.release}; ustalenie prawa: {p.right_date}.",
        f"System: {r.regime}; wysługa: {p.service_months} miesięcy; do art. 15aa: {p.qualifying_25_months} miesięcy.",
        f"Warunek stażu: {staz}.", "",
        f"Podstawa: {r.basis:.2f} zł; suma przed limitem: {r.raw_percent:.6f}%; limit: {r.cap}%; po limicie: {r.percent:.6f}%.",
        f"**Emerytura według reguł ustawy: {r.pension:.2f} zł/mies.**", "",
        f"Własne dodatki waloryzowane: {r.indexed_extra:.2f} zł; stałe: {r.fixed_extra:.2f} zł.",
        f"Wariant z własnymi dodatkami: {r.scenario:.2f} zł/mies.", "",
        "## Składniki procentowe", "",
    ]
    lines += [f"- {label}: {value:.6f} pp" for label, value in r.breakdown]

    lines += _net_and_earnings_section(p, r)
    lines += ["", "## Założenia i ograniczenia", ""]
    lines += [f"- {warning}" for warning in r.warnings]
    lines += [
        "- Staż i okresy podwyższeń muszą wynikać z dokumentacji jednostki. Aplikacja nie ustala prawa do świadczenia.",
        "- Symulacja nie uwzględnia PIT, składki zdrowotnej, 13./14. emerytury, potrąceń ani ograniczeń dorabiania.",
        "- Wypłaty od następnego pełnego miesiąca po zwolnieniu, nie wcześniej niż w miesiącu ustalenia prawa; bez wyrównań.",
        "- Własne dodatki poza limitami są hipotetyczne. Prognoza zakłada niezmienność prawa.",
        "", "## Waloryzacja — scenariusz użytkownika", "",
        "| Rok | Wzrost % | Inflacja % | Grudzień wariantu | Grudzień ustawa | Realnie | Netto | Rocznie | Narastająco |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in forecast(p, r):
        lines.append(f"| {row.year} | {row.rate} | {row.inflation} | {row.december:.2f} | "
                     f"{row.legal_december:.2f} | {row.real_december:.2f} | {row.net_december:.2f} | "
                     f"{row.annual:.2f} | {row.cumulative:.2f} |")

    lines += [
        "", "## Przepisy wybranej służby i systemu", "", service_rules(p),
        "", "## Źródła", "",
        "- [Ustawa, Dz.U. 2026 poz. 505](https://eli.gov.pl/eli/DU/2026/505/ogl/pol)",
        "- [Warunki podwyższeń, Dz.U. 2020 poz. 1611](https://eli.gov.pl/api/acts/DU/2020/1611/text.html)",
        "- [ZER MSWiA — kwoty](https://www.gov.pl/web/zermswia/wskazniki-i-kwoty)",
        "", "## Pełna konfiguracja", "", "```json",
        json.dumps(asdict(p), ensure_ascii=False, indent=2), "```", "",
    ]
    return "\n".join(lines)
