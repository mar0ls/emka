"""Reguły obliczeniowe emerytury funkcjonariusza. Nie zależą od GUI.

Numery artykułów dotyczą ustawy z 18.02.1994 o zaopatrzeniu emerytalnym
funkcjonariuszy (tekst jednolity: Dz.U. 2026 poz. 505).

Kwoty i procenty to `Decimal`. Zaokrąglamy dopiero na końcu, do grosza.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# Dzień, na który sprawdzono przepisy i kwoty urzędowe.
RULE_DATE = "2026-10-29"

SERVICES = ("Policja", "SG", "PSP", "ABW", "AW", "SKW", "SWW", "CBA", "SOP", "SW", "SM", "SC", "SCS")

# Podwyższenia z art. 15 ust. 2-3: punkty procentowe podstawy za jeden miesiąc.
# Stawki roczne (2/1/0,5 pp za rok) rozkładamy na 12 miesięcy,
# strefa wojny daje 0,5 pp za każdy rozpoczęty miesiąc.
BONUS_RATES = {
    "2%/rok": Decimal(2) / 12,
    "1%/rok": Decimal(1) / 12,
    "0,5%/rok": Decimal("0.5") / 12,
    "strefa wojny": Decimal("0.5"),
}

ZERO = Decimal(0)

# Najniższa emerytura obowiązująca od 1.03.2026 do 28.02.2027 (komunikat Prezesa ZUS).
MINIMUM_PENSION = Decimal("1978.49")
MINIMUM_VALID_FROM = date(2026, 3, 1)
MINIMUM_VALID_TO = date(2027, 2, 28)

# Podatek i składka zdrowotna od emerytury (przepisy na 2026 r.).
PIT_LOWER_RATE = Decimal("0.12")
PIT_UPPER_RATE = Decimal("0.32")
PIT_THRESHOLD = Decimal(120000)  # roczna podstawa, od której nadwyżka jest opodatkowana 32%
PIT_TAX_REDUCING_AMOUNT = Decimal(3600)  # rocznie; 300 zł miesięcznie (kwota wolna 30 000 zł)
HEALTH_RATE = Decimal("0.09")  # niepodlega odliczeniu od podatku

# Dorabianie (art. 41 ustawy mundurowej i art. 104 ustawy o FUS). Progi zmieniają się co kwartał
# (komunikat Prezesa ZUS w Monitorze Polskim); poniższe obowiązują od 1.09.2026 do 30.11.2026
# (M.P. 2026 poz. 839). Kwota maksymalnego zmniejszenia emerytury - od 1.03.2026 (M.P. 2026 poz. 220).
INCOME_LIMIT_LOW = Decimal("6463.20")  # 70% przeciętnego wynagrodzenia
INCOME_LIMIT_HIGH = Decimal("12003.10")  # 130% przeciętnego wynagrodzenia
MAX_REDUCTION = Decimal("989.41")
INCOME_LIMITS_VALID_TO = date(2026, 11, 30)
MAX_REDUCTION_VALID_TO = date(2027, 2, 28)  # kolejna waloryzacja od 1.03.2027
MAX_REDUCTION_SHARE = Decimal("0.25")  # art. 41 ust. 1 i 3: nigdy więcej niż 25% emerytury
FULL_PENSION_PERCENT = Decimal(75)  # art. 41 ust. 4: przy 75% podstawy zmniejszeń nie stosuje się

# Progi dat pierwszego przyjęcia do służby (art. 15, 15a, 15aa, rozdział 1a).
FIRST_DAY_AFTER_OLD_SYSTEM = date(1999, 1, 2)
FIRST_DAY_OF_CHAPTER_1A = date(2013, 1, 1)
ART_15AA_END = date(2003, 10, 1)  # pierwszy dzień, który już NIE kwalifikuje do art. 15aa

# Wymagana wysługa w pełnych miesiącach.
MONTHS_OLD_SYSTEM = 15 * 12
MONTHS_NEW_SYSTEM = 25 * 12
MONTHS_FOR_LONGEVITY_PAY = 32 * 12  # art. 5 ust. 1c

# Nazwy pól wpisywanych jako liczby - do czytelnych komunikatów o błędach.
FIELD_LABELS = {
    "service_months": "Łączna wysługa służby (miesiące)",
    "qualifying_25_months": "Miesiące do warunku art. 15aa",
    "pre_contrib_months": "Składkowe przed służbą (miesiące)",
    "pre_noncontrib_months": "Nieskładkowe przed służbą (miesiące)",
    "post_contrib_months": "Do doliczenia po służbie (miesiące)",
    "forecast_years": "Horyzont symulacji (lata)",
}
MONTH_FIELDS = tuple(name for name in FIELD_LABELS if name.endswith("_months"))


def number(value, label="Liczba", minimum=ZERO, maximum=Decimal("1000000000")):
    """Zamienia tekst (z przecinkiem lub kropką, ze spacjami) na Decimal."""
    try:
        result = Decimal(str(value).strip().replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label}: wpisz poprawną liczbę.") from None
    if not result.is_finite() or not minimum <= result <= maximum:
        raise ValueError(f"{label}: dopuszczalny zakres {minimum}–{maximum}.")
    return result


def integer(value, label, minimum=0, maximum=1200):
    """Jak `number`, ale wymaga liczby całkowitej."""
    result = number(value, label, Decimal(minimum), Decimal(maximum))
    if result != result.to_integral_value():
        raise ValueError(f"{label}: wymagana liczba całkowita.")
    return int(result)


def money(value):
    """Zaokrągla do grosza (połówki w górę)."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_date(value, label):
    """Przyjmuje RRRR-MM-DD oraz DD.MM.RRRR."""
    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"{label}: wpisz datę jako RRRR-MM-DD albo DD.MM.RRRR.")


def month_number(day):
    """Kolejny numer miesiąca kalendarzowego - ułatwia porównania i pętle."""
    return day.year * 12 + day.month - 1


def parse_month(value):
    """Przyjmuje RRRR-MM oraz MM.RRRR; zwraca `month_number`."""
    text = str(value).strip()
    for pattern in ("%Y-%m", "%m.%Y"):
        try:
            return month_number(datetime.strptime(text, pattern).date())
        except ValueError:
            continue
    raise ValueError("Okres podwyższenia: użyj formatu RRRR-MM.")


def full_months_between(start, end):
    """Pełne miesiące od `start` do `end`, obie daty włącznie."""
    after_end = end + timedelta(days=1)
    months = (after_end.year - start.year) * 12 + after_end.month - start.month
    if after_end.day < start.day:
        months -= 1
    return max(0, months)


@dataclass
class Bonus:
    """Okres, za który jednostka zaliczyła podwyższenie emerytury."""
    name: str = "Warunki szczególne"
    kind: str = "0,5%/rok"
    start: str = "2005-01"
    end: str = "2005-12"
    confirmed: bool = False


@dataclass
class Extra:
    """Własny dodatek użytkownika - tylko do symulacji, poza wynikiem z ustawy."""
    name: str = "Własny wariant"
    unit: str = "pp podstawy"
    value: str = "0"
    indexed: bool = True
    enabled: bool = True


@dataclass
class AnnualPay:
    """Jeden rok z 10 branych do podstawy wymiaru (art. 18f ust. 3)."""
    year: int = 2016
    pay: str = "120000"
    reference: str = "100000"


@dataclass
class Profile:
    name: str = "Mój scenariusz"
    service: str = "Policja"
    first_entry: str = "2001-01-01"
    release: str = "2026-10-31"
    right_date: str = "2026-11-01"
    regime: str = "auto"  # "auto", "15aa" albo "18h"
    new_system: bool | None = None  # None = wybierz według daty
    service_months: int = 310
    qualifying_25_months: int = 310
    pre_contrib_months: int = 0
    pre_noncontrib_months: int = 0
    post_contrib_months: int = 0
    post_conditions: bool = False
    disability: bool = False
    medal: bool = False
    special_case: bool = False
    fus_service_used: bool = False
    exclusion: bool = False
    base_mode: str = "gotowa podstawa"
    base: str = "10000"
    salary: str = "8000"
    permanent: str = "1000"
    annual_award: str = "12000"
    longevity: str = "0"
    current_reference: str = "10000"
    annual_pay: list[AnnualPay] = field(default_factory=list)
    minimum: str = str(MINIMUM_PENSION)
    fus_pension: str = "0"
    bonuses: list[Bonus] = field(default_factory=list)
    extras: list[Extra] = field(default_factory=list)
    pit2: bool = True  # czy emerytura jest rozliczana z kwotą zmniejszającą podatek (300 zł miesięcznie)
    work_income: str = "0"  # miesięczny przychód brutto z pracy w cywilnej firmie
    income_limit_low: str = str(INCOME_LIMIT_LOW)
    income_limit_high: str = str(INCOME_LIMIT_HIGH)
    max_reduction: str = str(MAX_REDUCTION)
    forecast_years: int = 20
    growth: str = "4"
    inflation: str = "2.5"
    overrides: dict = field(default_factory=dict)  # {"2030": {"growth": "3", "inflation": "2"}}


@dataclass
class Result:
    regime: str
    basis: Decimal
    raw_percent: Decimal  # suma składników przed limitem
    percent: Decimal  # po limicie
    cap: Decimal
    pension: Decimal  # emerytura wg reguł ustawy
    indexed_extra: Decimal
    fixed_extra: Decimal
    breakdown: list[tuple[str, Decimal]]
    warnings: list[str]
    eligible: bool
    missing_months: int

    @property
    def scenario(self):
        """Emerytura z własnymi dodatkami."""
        return money(self.pension + self.indexed_extra + self.fixed_extra)


@dataclass
class ForecastRow:
    year: int
    rate: Decimal  # waloryzacja faktycznie zastosowana w tym roku (0 = brak)
    inflation: Decimal
    before_march: Decimal  # kwota miesięczna przed marcową waloryzacją
    december: Decimal  # z własnymi dodatkami
    legal_december: Decimal  # tylko reguły ustawy
    real_december: Decimal  # w cenach początku pierwszego roku
    net_december: Decimal  # po podatku i składce zdrowotnej (bez dorabiania)
    annual: Decimal  # suma wypłat w roku
    cumulative: Decimal


def select_regime(p):
    """Zwraca oznaczenie przepisów, według których liczymy emeryturę.

    Rozstrzyga data pierwszego przyjęcia do służby oraz (opcjonalne) wybory
    z art. 15ab (15aa) i art. 18h (rozdział 1a). Przy sprzecznych ustawieniach
    zgłasza błąd z podpowiedzią, co poprawić.
    """
    first = parse_date(p.first_entry, "Pierwsze przyjęcie")
    customs = p.service in ("SC", "SCS")

    if p.regime not in ("auto", "15aa", "18h"):
        raise ValueError("Nieznany wybór zasad.")
    if p.new_system is False and first >= FIRST_DAY_OF_CHAPTER_1A:
        raise ValueError(
            "Przyjęcie od 1.01.2013 wymaga zaznaczenia systemu 25 lat / 60%. "
            "Starszy system może wynikać z wcześniejszej służby — wtedy podaj właściwą wcześniejszą datę.")
    if p.new_system is False and p.regime == "18h":
        raise ValueError("Art. 18h oznacza wybór nowego systemu — zaznacz pole 25 lat / 60%.")
    if p.new_system is True and p.regime == "15aa":
        raise ValueError("Wybierz jeden wariant: nowy system 25 lat / 60% albo art. 15aa starszego systemu.")

    # Rozdział 1a: z mocy daty albo z wyboru (art. 18h).
    if p.regime == "18h" or p.new_system is True:
        if first >= FIRST_DAY_OF_CHAPTER_1A:
            return "18e"
        if p.service == "SM":
            raise ValueError("Art. 18h wymaga właściwego pierwszego przyjęcia przed 2013 r. (SM: indywidualna weryfikacja).")
        return "18h → 18e"

    if p.regime == "15aa":
        if not FIRST_DAY_AFTER_OLD_SYSTEM <= first < ART_15AA_END:
            raise ValueError("Art. 15aa: pierwsze przyjęcie musi przypadać 2.01.1999–30.09.2003.")
        return "15d → 15aa" if customs else "15aa"

    if first >= FIRST_DAY_OF_CHAPTER_1A:
        return "18e"
    if first < FIRST_DAY_AFTER_OLD_SYSTEM:
        return "15e → 15" if customs else "15"
    return "15d → 15a" if customs else "15a"


SERVICE_NAMES = {
    "Policja": "Policja", "SG": "Straż Graniczna", "PSP": "Państwowa Straż Pożarna",
    "ABW": "Agencja Bezpieczeństwa Wewnętrznego", "AW": "Agencja Wywiadu",
    "SKW": "Służba Kontrwywiadu Wojskowego", "SWW": "Służba Wywiadu Wojskowego",
    "CBA": "Centralne Biuro Antykorupcyjne", "SOP": "Służba Ochrony Państwa",
    "SW": "Służba Więzienna", "SM": "Straż Marszałkowska", "SC": "Służba Celna",
    "SCS": "Służba Celno-Skarbowa",
}

_SKW_NOTE = ("funkcjonariusz podlega ustawie z 18.02.1994, mimo właściwości wojskowego organu. "
             "Żołnierz zawodowy podlega odrębnej ustawie. Sprawdź daty stosowania podwyższeń (§6a).")

# Uwagi szczególne dla poszczególnych służb (pokazywane w zakładce „Dane” i w raporcie).
SERVICE_NOTES = {
    "PSP": "PSP: samo pełnienie służby nie daje +0,5 pp. W starszym systemie §4 pkt 3 wymaga odpowiednich działań ratowniczych lub kierowania nimi na miejscu przez co najmniej 30 dni w roku.",
    "SG": "SG: możliwe potwierdzone podwyższenia m.in. za służbę na jednostkach pływających, loty i szczególne warunki. Normy z rozporządzenia nie wynikają automatycznie ze stanowiska.",
    "ABW": "ABW: fizyczne zwalczanie terroryzmu wymaga kwalifikacji i działań lub szkolenia; warunki §2 i daty stosowania §6a trzeba potwierdzić.",
    "AW": "AW: w starszym systemie wywiad za granicą wymaga wykonywania lub kierowania czynnościami operacyjno-rozpoznawczymi; strefa wojny jest odrębnym tytułem.",
    "SKW": "SKW: " + _SKW_NOTE,
    "SWW": "SWW: " + _SKW_NOTE,
    "SW": "SW: szczególne podwyższenie za opiekę nad określonymi osadzonymi wymaga warunków §4 pkt 4, w tym 8 miesięcy odpowiednich zadań w roku.",
    "SM": "SM: także w starszym systemie podstawa jest ustalana z 10 kolejnych lat (art. 5 ust. 1a). Okresy wcześniejszego zatrudnienia muszą odpowiadać stanowiskom wymienionym w ustawie.",
    "SC": "SC: art. 15d/15e, wcześniejsza służba i tryb mianowania/przekształcenia wymagają weryfikacji. Okresy art. 18ga tylko z zaświadczenia; termin wniosku 30.06.2026. Podstawa z 10 lat.",
    "SCS": "SCS: art. 15d/15e, wcześniejsza służba i tryb przekształcenia wymagają weryfikacji. Art. 18ga ust. 2: limit 8 lat 7 miesięcy i zaświadczenie; termin wniosku 30.06.2026. Podstawa z 10 lat.",
    "SOP": "SOP: uwzględnij wcześniejszą służbę w BOR. Weryfikacja szczególnych okresów wymaga również dat stosowania rozporządzenia (§6a).",
    "CBA": "CBA: podwyższenia wymagają potwierdzenia norm i odpowiednich dat stosowania przepisów (§6a), a nie wyłącznie służby w CBA.",
    "Policja": "Policja: podwyższenia szczególne wymagają warunków rozporządzenia. Art. 15aa jest wyborem tylko dla właściwych przyjęć 2.01.1999–30.09.2003; nie wynika automatycznie z 25 lat służby.",
}


def pension_authority(service):
    """Organ emerytalny właściwy dla służby (art. 32 ust. 1)."""
    if service in ("SKW", "SWW"):
        return "wojskowy organ emerytalny (art. 32 ust. 1 pkt 1a)"
    if service == "SW":
        return "organ emerytalny określony przez Ministra Sprawiedliwości (art. 32 ust. 1 pkt 2)"
    return "właściwy organ emerytalny MSWiA (art. 32 ust. 1 pkt 1)"


def service_rules(p):
    """Krótkie objaśnienie przepisów właściwych dla służby i systemu (bez liczenia emerytury)."""
    try:
        regime = select_regime(p)
        modern = "18e" in regime
        if modern:
            formula = "25 lat: 60%; dalsza służba 3 pp/rok. Limit 75%, z Medalem 76%."
        else:
            formula = ("15 lat: 40%; dalsza służba 2,6 pp/rok. Limit 75%, z inwalidztwem 80%; "
                       "z Medalem odpowiednio 76/81%.")
        if modern or p.service in ("SC", "SCS", "SM"):
            base = "10 kolejnych lat, przeliczenie wskaźnikowe art. 18f"
        else:
            base = "należne uposażenie na ostatnim stanowisku — art. 5"
        selection = f"System: art. {regime}. {formula}\nPodstawa: {base}."
        if modern:
            selection += " Podwyższenia: strefa wojny i Medal; bez rocznych 0,5/1/2 pp i +15 pp."
    except ValueError as exc:
        selection = "Sprawdź wybór systemu: " + str(exc)

    return (f"{SERVICE_NAMES.get(p.service, p.service)} · reguły sprawdzone {RULE_DATE}\n"
            f"{selection}\n"
            f"Organ: {pension_authority(p.service)}.\n"
            f"{SERVICE_NOTES.get(p.service, '')}\n"
            "Źródła: Dz.U. 2026 poz. 505; podwyższenia: Dz.U. 2020 poz. 1611. "
            "Szczegóły i wyjątki: zakładka Przepisy.")


def compute_basis(p, modern, service_months, warnings):
    """Miesięczna podstawa wymiaru emerytury (art. 5 i 18f).

    Trzy tryby: wpisana gotowa kwota, składniki ostatniego uposażenia
    (starszy system) albo średnia wskaźników z 10 kolejnych lat.
    """
    ten_year_rule = modern or p.service in ("SM", "SC", "SCS")

    if p.base_mode == "gotowa podstawa":
        basis = number(p.base, "Podstawa", Decimal("0.01"))
        warnings.append(
            "Podstawa wpisana ręcznie: musi uwzględniać art. 5/18f, wyłączenia "
            "i ewentualne waloryzacje między zwolnieniem a ustaleniem prawa.")
        if ten_year_rule:
            warnings.append(
                "Dla wybranego systemu/służby podstawa wymaga 10 kolejnych lat i przeliczenia "
                "z art. 18f; wpisana kwota powinna być już tak ustalona.")
        return basis

    if p.base_mode not in ("składniki uposażenia", "10 kolejnych lat"):
        raise ValueError("Nieznany sposób ustalenia podstawy.")

    # Świadczenie za długoletnią służbę wlicza się dopiero po 32 latach wysługi.
    # Sprawdzamy je tylko tam, gdzie faktycznie je dodajemy.
    longevity = number(p.longevity, "Świadczenie za długoletnią służbę")
    if longevity and service_months < MONTHS_FOR_LONGEVITY_PAY:
        raise ValueError("Świadczenie za długoletnią służbę w podstawie wymaga 32 lat wysługi.")

    if p.base_mode == "składniki uposażenia":
        if ten_year_rule:
            raise ValueError("Ten system wymaga podstawy z 10 lat. Wybierz formularz 10 lat lub gotową podstawę.")
        award_per_month = number(p.annual_award, "Nagroda roczna") / 12
        return money(number(p.salary, "Uposażenie") + number(p.permanent, "Dodatki stałe")
                     + award_per_month + longevity)

    # Tryb „10 kolejnych lat”.
    if not ten_year_rule:
        raise ValueError("Dla starszego systemu tej służby użyj ostatniego uposażenia albo gotowej podstawy.")
    return ten_year_basis(p, longevity, warnings)


def ten_year_basis(p, longevity, warnings):
    """Art. 18f ust. 3: średnia z 10 rocznych wskaźników × przeciętne uposażenie + świadczenie za długoletnią służbę."""
    if len(p.annual_pay) != 10:
        raise ValueError("Podstawa z 10 lat: wymagane dokładnie 10 wierszy.")

    # Rok wpisujemy czasem jako tekst, dlatego najpierw sprawdzamy wszystkie lata, potem sortujemy.
    rows = [(integer(a.year, "Rok", 1900, 2200), a) for a in p.annual_pay]
    rows.sort(key=lambda row: row[0])
    years = [year for year, _ in rows]
    if years != list(range(years[0], years[0] + 10)):
        raise ValueError("Podstawa: lata muszą być kolejne i nie mogą się powtarzać.")
    if years[-1] > parse_date(p.release, "Zwolnienie").year:
        raise ValueError("Podstawa: wybrano rok po zwolnieniu.")

    # Każdy roczny stosunek zaokrąglamy do 0,01% (art. 18f ust. 3 pkt 2), dopiero potem uśredniamy.
    ratios = []
    for _, row in rows:
        pay = number(row.pay, "Roczne uposażenie")
        average = number(row.reference, "Roczne przeciętne uposażenie", Decimal("0.01"))
        ratios.append(money(pay / average * 100))
    index = sum(ratios) / 10 / 100

    current_average = number(p.current_reference, "Przeciętne uposażenie na dzień zwolnienia", Decimal("0.01"))
    warnings.append("Dane roczne muszą być należne i skorygowane według art. 18f; "
                    "mieszane służby w roku wymagają wcześniejszego przeliczenia.")
    return money(index * current_average + longevity)


def bonus_percent(p, modern, first, release, service_months, warnings):
    """Suma podwyższeń (w pp podstawy) z potwierdzonych okresów.

    Za ten sam miesiąc liczymy tylko najwyższe podwyższenie (art. 17).
    """
    rate_per_month = {}  # numer miesiąca -> najwyższa stawka
    overlap = False
    first_month, last_month = month_number(first), month_number(release)

    for bonus in p.bonuses:
        if bonus.kind not in BONUS_RATES:
            raise ValueError("Nieznany rodzaj podwyższenia.")
        if not bonus.confirmed:
            raise ValueError(f"{bonus.name}: potwierdź warunki i zaliczenie okresu przez jednostkę.")
        if modern and bonus.kind != "strefa wojny":
            raise ValueError("Rozdział 1a nie przewiduje rocznych podwyższeń 0,5/1/2%. Usuń je lub zmień system.")

        start, end = parse_month(bonus.start), parse_month(bonus.end)
        if not first_month <= start <= end <= last_month:
            raise ValueError(f"{bonus.name}: okres musi mieścić się między pierwszym przyjęciem a zwolnieniem.")

        for month in range(start, end + 1):
            overlap = overlap or month in rate_per_month
            rate_per_month[month] = max(rate_per_month.get(month, ZERO), BONUS_RATES[bonus.kind])

    if len(rate_per_month) > service_months:
        raise ValueError("Okresy podwyższeń przekraczają podaną wysługę służby.")
    if overlap:
        warnings.append("Nakładające się podwyższenia: za ten sam miesiąc wybrano najwyższe, zgodnie z art. 17.")
    if rate_per_month:
        warnings.append("Podwyższenia przyjęto z potwierdzonych okresów; aplikacja nie weryfikuje "
                        "norm rocznych, incydentów ani historycznych uprawnień jednostki.")
    return sum(rate_per_month.values(), ZERO)


@dataclass
class _Input:
    """Zwalidowane dane liczbowe i daty (żeby nie zmieniać przekazanego profilu)."""
    months: dict
    first: date
    release: date
    right: date


def _read_input(p):
    """Zamienia pola tekstowe profilu na liczby i daty oraz sprawdza ich spójność."""
    if p.service not in SERVICES:
        raise ValueError("Nieznana służba.")
    months = {name: integer(getattr(p, name), FIELD_LABELS[name]) for name in MONTH_FIELDS}
    first = parse_date(p.first_entry, "Pierwsze przyjęcie")
    release = parse_date(p.release, "Zwolnienie")
    right = parse_date(p.right_date, "Ustalenie prawa")

    if release < date(2026, 1, 1):
        raise ValueError("EMKA stosuje reguły zweryfikowane w 2026 r.; nie odtwarza historycznych decyzji sprzed 2026 r.")
    if first > release or right < release or right.year > 2200:
        raise ValueError("Wymagana kolejność: pierwsze przyjęcie ≤ zwolnienie ≤ ustalenie prawa (do 2200 r.).")

    # Wysługa nie może być dłuższa niż czas między pierwszym przyjęciem a zwolnieniem.
    # (Okresy równorzędne sprzed pierwszego przyjęcia wlicz, podając wcześniejszą datę początku.)
    available = full_months_between(first, release)
    if months["service_months"] > available:
        raise ValueError(
            f"Wysługa ({months['service_months']} mies.) jest dłuższa niż czas od pierwszego przyjęcia "
            f"do zwolnienia ({available} pełnych mies.). Popraw daty albo liczbę miesięcy.")
    if months["qualifying_25_months"] > months["service_months"]:
        raise ValueError("Miesiące do warunku art. 15aa nie mogą przekraczać łącznej wysługi.")
    return _Input(months, first, release, right)


def _civil_periods_percent(m, regime_is_art15, regime_is_15aa, breakdown, warnings):
    """Dodaje do `breakdown` cywilne okresy przed służbą (art. 15 ust. 1 pkt 2-4 oraz art. 15aa ust. 3)."""
    pre_contrib, pre_noncontrib = m["pre_contrib_months"], m["pre_noncontrib_months"]

    if regime_is_art15:
        # Pierwsze 3 lata składkowe po 2,6 pp, dalsze po 1,3 pp, nieskładkowe po 0,7 pp za rok.
        first_three_years = min(36, pre_contrib)
        further = max(0, pre_contrib - 36)
        contrib = Decimal(first_three_years) * Decimal("2.6") / 12 + Decimal(further) * Decimal("1.3") / 12
        breakdown.append(("Okresy składkowe przed służbą", contrib))
        breakdown.append(("Okresy nieskładkowe (już po ograniczeniach FUS)",
                          Decimal(pre_noncontrib) * Decimal("0.7") / 12))
        return

    if regime_is_15aa and m["qualifying_25_months"] >= MONTHS_NEW_SYSTEM:
        breakdown.append(("Okresy składkowe przed służbą — art. 15aa", Decimal(pre_contrib) * Decimal("1.3") / 12))
        warnings.append("Wybór art. 15aa i doliczenie okresów cywilnych wymagają sprawdzenia skutków dla OFE oraz emerytury FUS.")
    elif pre_contrib:
        warnings.append("Okresy składkowe przed służbą nie podwyższają wyniku w wybranym systemie lub nie spełniono 25 lat do art. 15aa.")

    if pre_noncontrib:
        warnings.append("Okresy nieskładkowe przed służbą pominięto w wybranym systemie.")


def _apply_minimum(p, pension, regime_is_art15, regime_is_15aa, eligible, warnings):
    """Podnosi emeryturę do najniższej emerytury (art. 18 ust. 2-3, w rozdziale 1a art. 18g)."""
    minimum = number(p.minimum, "Minimum emerytury")
    fus = number(p.fus_pension, "Emerytura FUS")

    if not minimum:
        warnings.append("Wyłączono uzupełnienie do najniższej emerytury.")
    elif eligible:
        # Art. 18 ust. 3: przy art. 15a/15d i w rozdziale 1a liczy się suma z emeryturą FUS.
        # Przy art. 15 i 15aa obowiązuje pełna kwota minimum (ust. 2).
        sum_rule = not regime_is_art15 and not regime_is_15aa
        floor = max(ZERO, minimum - fus) if sum_rule else minimum
        if pension < floor:
            warnings.append("Zastosowano minimalną kwotę świadczenia (art. 18 ust. 2–3 / 18g); "
                            "procent pokazano przed uzupełnieniem minimum.")
            pension = money(floor)

    return pension, minimum


def _custom_extras(p, basis, pension):
    """Sumuje własne dodatki: osobno waloryzowane i stałe."""
    indexed, fixed = ZERO, ZERO
    for extra in p.extras:
        if not extra.enabled:
            continue
        value = number(extra.value, f"Dodatek {extra.name}")
        if extra.unit == "pp podstawy":
            amount = basis * value / 100
        elif extra.unit == "% emerytury":
            amount = pension * value / 100
        elif extra.unit == "zł miesięcznie":
            amount = value
        else:
            raise ValueError("Nieznana jednostka własnego dodatku.")
        if extra.indexed:
            indexed += amount
        else:
            fixed += amount
    return indexed, fixed


def calculate(p):
    """Główne obliczenie: emerytura brutto według reguł ustawy oraz wariant z własnymi dodatkami."""
    data = _read_input(p)
    m = data.months
    service_months = m["service_months"]

    if p.special_case or p.fus_service_used or p.exclusion:
        raise ValueError("Przypadek wymaga indywidualnego rozstrzygnięcia: art. 15c/10 lub służba już "
                         "uwzględniona w emeryturze FUS. Zwykły kalkulator został zablokowany.")

    regime = select_regime(p)
    modern = "18e" in regime  # rozdział 1a: 25 lat, 60%
    is_art15 = regime in ("15", "15e → 15")
    is_15aa = "15aa" in regime

    warnings = ["Szacunek brutto. Spełnienie warunku stażu nie przesądza o prawie do emerytury; "
                "decyzję wydaje właściwy organ."]
    if data.release > date.fromisoformat(RULE_DATE):
        checked_on = date.fromisoformat(RULE_DATE).strftime("%d.%m.%Y")
        warnings.append(f"Przyszła data zwolnienia: przyjęto niezmienność reguł zweryfikowanych {checked_on}.")
    if p.service in ("SC", "SCS"):
        warnings.append("SC/SCS: wcześniejszą służbę, mianowanie i okresy art. 18ga należy sprawdzić "
                        "w zaświadczeniu; nietypowe początki przed 15.09.1999 wymagają indywidualnej analizy.")

    basis = compute_basis(p, modern, service_months, warnings)
    if basis <= ZERO:
        raise ValueError("Podstawa musi być większa od zera.")

    # Prawo do emerytury: staż liczony w pełnych miesiącach.
    required_months = MONTHS_NEW_SYSTEM if modern else MONTHS_OLD_SYSTEM
    missing_months = max(0, required_months - service_months)
    eligible = missing_months == 0

    # Składniki procentowe podstawy.
    base_percent = Decimal(60 if modern else 40)
    yearly_step = Decimal(3 if modern else "2.6")
    further_service = Decimal(max(0, service_months - required_months)) * yearly_step / 12
    breakdown = [
        ("60% za 25 lat (art. 18e)" if modern else "40% za 15 lat (art. 15/15a)", base_percent),
        ("Dalsza służba — pełne miesiące", further_service),
    ]
    _civil_periods_percent(m, is_art15, is_15aa, breakdown, warnings)
    breakdown.append(("Podwyższenia za potwierdzone okresy",
                      bonus_percent(p, modern, data.first, data.release, service_months, warnings)))

    if p.disability:
        if modern:
            raise ValueError("+15 pp za inwalidztwo związane ze służbą nie przysługuje w rozdziale 1a.")
        breakdown.append(("Inwalidztwo związane ze służbą — art. 15 ust. 4", Decimal(15)))
    if p.medal:
        breakdown.append(("Medal im. Andrzeja Struja", Decimal(1)))

    # Okresy cywilne po zwolnieniu (art. 14 / 15aa ust. 4-6) - na wniosek, tylko gdy emerytura < 75%.
    can_add_post_service = is_art15 or (is_15aa and m["qualifying_25_months"] >= MONTHS_NEW_SYSTEM)
    if m["post_contrib_months"]:
        if not can_add_post_service:
            raise ValueError("Okresy po służbie: wymagany art. 15/15e albo spełnienie szczególnego warunku 25 lat w art. 15aa.")
        if not p.post_conditions:
            raise ValueError("Doliczenie okresów po służbie wymaga potwierdzenia warunków wniosku i — w art. 14 — wieku/inwalidztwa.")
        if sum((value for _, value in breakdown), ZERO) >= 75:
            warnings.append("Okresów po służbie nie doliczono: emerytura przed doliczeniem wynosi co najmniej 75%.")
        else:
            breakdown.append(("Okresy składkowe po służbie (na wniosek)",
                              Decimal(m["post_contrib_months"]) * Decimal("1.3") / 12))

    # Limit: 75%, z inwalidztwem 80%, z Medalem o 1 pp więcej (art. 18 ust. 1-1a, art. 18g).
    raw_percent = sum((value for _, value in breakdown), ZERO)
    cap = Decimal(75 + (5 if p.disability else 0) + (1 if p.medal else 0))
    percent = min(raw_percent, cap) if eligible else ZERO
    pension = money(basis * percent / 100)

    pension, minimum = _apply_minimum(p, pension, is_art15, is_15aa, eligible, warnings)
    if minimum == MINIMUM_PENSION and not MINIMUM_VALID_FROM <= data.right <= MINIMUM_VALID_TO:
        amount = str(MINIMUM_PENSION).replace(".", ",")
        warnings.append(f"Minimum {amount} zł pochodzi z marca 2026–lutego 2027. "
                        "Dla podanej daty sprawdź i zmień kwotę.")

    indexed_extra, fixed_extra = _custom_extras(p, basis, pension)
    if indexed_extra or fixed_extra:
        warnings.append("Własne dodatki są wyłącznie symulacją poza wynikiem ustawowym i jego limitami; "
                        "nie oznaczają prawa do wypłaty.")
    if not eligible:
        warnings.append(f"Brakuje {missing_months} pełnych miesięcy służby do wymaganego stażu. "
                        "Nie wyliczono świadczenia ani dodatków.")
        indexed_extra = fixed_extra = ZERO

    return Result(regime, basis, raw_percent, percent, cap, pension, money(indexed_extra),
                  money(fixed_extra), breakdown, warnings, eligible, missing_months)


@dataclass
class NetPension:
    gross: Decimal
    health: Decimal  # składka zdrowotna
    tax: Decimal  # miesięczna zaliczka na PIT
    net: Decimal  # kwota "na rękę"


def net_pension(gross, use_tax_reducing_amount=True):
    """Emerytura po odliczeniu składki zdrowotnej (9%) i zaliczki na PIT (12%/32%).

    Zaliczkę liczymy tak jak płatnik: roczny podatek podzielony na 12 miesięcy i zaokrąglony do pełnych
    złotych. Kwota zmniejszająca (3600 zł rocznie) obowiązuje po złożeniu PIT-2. Wynik dotyczy samej
    emerytury - inne dochody mogą zmienić podatek przy rozliczeniu rocznym.
    """
    annual = gross * 12
    if annual <= PIT_THRESHOLD:
        yearly_tax = annual * PIT_LOWER_RATE
    else:
        yearly_tax = PIT_THRESHOLD * PIT_LOWER_RATE + (annual - PIT_THRESHOLD) * PIT_UPPER_RATE
    if use_tax_reducing_amount:
        yearly_tax -= PIT_TAX_REDUCING_AMOUNT
    tax = (max(ZERO, yearly_tax) / 12).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    health = money(gross * HEALTH_RATE)
    return NetPension(gross, health, tax, gross - health - tax)


def is_exempt_from_reduction(p, result):
    """Art. 41 ust. 4: emerytura równa co najmniej 75% podstawy (bez +15 pp za inwalidztwo) nie jest zmniejszana."""
    percent = result.raw_percent - (Decimal(15) if p.disability else ZERO)
    percent_cap = FULL_PENSION_PERCENT + (1 if p.medal else 0)
    return min(percent, percent_cap) >= FULL_PENSION_PERCENT


def reduction_for(income, pension, low, high, max_reduction, exempt=False):
    """Zwraca (strefa, kwota zmniejszenia) dla miesięcznego przychodu `income`.

    - do 70% przeciętnego wynagrodzenia: bez zmniejszenia;
    - 70%-130%: o kwotę przekroczenia, ale nie więcej niż kwota maksymalna i 25% emerytury;
    - powyżej 130%: o 25% emerytury (mundurowi - w odróżnieniu od ZUS - nie tracą całości).
    """
    quarter = money(pension * MAX_REDUCTION_SHARE)
    if exempt or income <= low:
        return "below", ZERO
    if income <= high:
        return "reduced", min(money(income - low), max_reduction, quarter)
    return "over", quarter


@dataclass
class EarningsEffect:
    income: Decimal
    low: Decimal
    high: Decimal
    exempt: bool
    zone: str  # "below", "reduced" albo "over"
    reduction: Decimal
    pension_before: Decimal
    pension_after: Decimal
    net_before: NetPension
    net_after: NetPension
    warnings: list[str]


def _earnings_limits(p):
    low = number(p.income_limit_low, "Próg 70% przeciętnego wynagrodzenia", Decimal("0.01"))
    high = number(p.income_limit_high, "Próg 130% przeciętnego wynagrodzenia", Decimal("0.01"))
    max_reduction = number(p.max_reduction, "Kwota maksymalnego zmniejszenia")
    if low >= high:
        raise ValueError("Próg 70% musi być niższy od progu 130% przeciętnego wynagrodzenia.")
    return low, high, max_reduction


def earnings_effect(p, result, today=None):
    """Ile emerytury traci emeryt dorabiający w cywilnej firmie. Zwraca None, gdy emerytura nie przysługuje.

    `today` służy tylko do testów (domyślnie dzisiejsza data).
    """
    if not result.eligible:
        return None
    income = number(p.work_income, "Przychód z pracy")
    low, high, max_reduction = _earnings_limits(p)
    exempt = is_exempt_from_reduction(p, result)
    zone, reduction = reduction_for(income, result.pension, low, high, max_reduction, exempt)

    warnings = ["Przychód to kwota brutto z działalności objętej ubezpieczeniem społecznym "
                "(umowa o pracę, zlecenie, własna firma). Umowa o dzieło zwykle nie wlicza się."]
    if exempt:
        warnings.append("Emerytura wynosi co najmniej 75% podstawy — dorabiać można bez zmniejszeń (art. 41 ust. 4).")
    # Ostrzegamy tylko wtedy, gdy po terminie w polach nadal stoją wartości domyślne - czyli nikt ich nie zaktualizował.
    today = today or date.today()
    if today > INCOME_LIMITS_VALID_TO and (low, high) == (INCOME_LIMIT_LOW, INCOME_LIMIT_HIGH):
        warnings.append(f"Progi przychodu obowiązywały do {INCOME_LIMITS_VALID_TO:%d.%m.%Y}. "
                        "Sprawdź aktualny komunikat Prezesa ZUS (Monitor Polski) i wpisz nowe wartości.")
    if today > MAX_REDUCTION_VALID_TO and max_reduction == MAX_REDUCTION:
        warnings.append(f"Kwota maksymalnego zmniejszenia obowiązywała do {MAX_REDUCTION_VALID_TO:%d.%m.%Y}. "
                        "Sprawdź aktualny komunikat Prezesa ZUS i wpisz nową kwotę.")
    if not exempt and zone != "below":
        # Skok przy progu 130%: tuż poniżej obowiązuje kwota maksymalna, powyżej - stałe 25% emerytury.
        just_below = reduction_for(high, result.pension, low, high, max_reduction)[1]
        just_above = reduction_for(high + Decimal("0.01"), result.pension, low, high, max_reduction)[1]
        if just_above > just_below:
            warnings.append(f"Uwaga na próg 130% ({high:.2f} zł): przy przychodzie do tej kwoty zmniejszenie wynosi "
                            f"najwyżej {just_below:.2f} zł, a o 1 gr wyżej od razu {just_above:.2f} zł (25% emerytury, "
                            "bez kwoty maksymalnej - art. 41 ust. 3).")
    warnings.append("Zmniejszenie rozlicza się po zakończeniu roku (rocznie albo miesięcznie na wniosek); "
                    "tu pokazano miesięczny skutek przy stałym przychodzie. Z tekstu ustawy nie wynika wyłączenie ze względu na wiek; potwierdź to w organie emerytalnym.")

    after = result.pension - reduction
    return EarningsEffect(income, low, high, exempt, zone, reduction, result.pension, after,
                          net_pension(result.pension, p.pit2), net_pension(after, p.pit2), warnings)


def earnings_table(p, result):
    """Przykładowe przychody i skutek dla emerytury: [(przychód, zmniejszenie, brutto po, netto po)]."""
    low, high, max_reduction = _earnings_limits(p)
    exempt = is_exempt_from_reduction(p, result)
    samples = [low, (low + high) / 2, high, high + 1000]
    rows = []
    for income in (money(x) for x in samples):
        _, reduction = reduction_for(income, result.pension, low, high, max_reduction, exempt)
        after = result.pension - reduction
        rows.append((income, reduction, after, net_pension(after, p.pit2).net))
    return rows


def _read_overrides(p, first_year, years):
    """Roczne wyjątki od domyślnej waloryzacji i inflacji: {rok: (wzrost, inflacja)}."""
    overrides = {}
    for year_text, rates in p.overrides.items():
        year = integer(year_text, "Rok zmiany", first_year, first_year + years - 1)
        if not isinstance(rates, dict) or set(rates) != {"growth", "inflation"}:
            raise ValueError("Zmiana roczna wymaga pól growth i inflation.")
        overrides[year] = (number(rates["growth"], "Wzrost roczny", ZERO, Decimal(100)),
                           number(rates["inflation"], "Inflacja roczna", Decimal(-50), Decimal(100)))
    return overrides


def forecast(p, result):
    """Symulacja miesięcznej emerytury i wypłat rocznych z coroczną waloryzacją od 1 marca.

    - Wypłaty zaczynają się od następnego pełnego miesiąca po zwolnieniu,
      nie wcześniej niż w miesiącu ustalenia prawa. Niepełnych miesięcy nie liczymy.
    - Waloryzacja obejmuje tylko emerytury z prawem ustalonym przed 1 marca (art. 6 pkt 1 lit. a).
    - Wartość realna: grudzień w cenach początku pierwszego roku symulacji.
    """
    years = integer(p.forecast_years, FIELD_LABELS["forecast_years"], 1, 60)
    default_growth = number(p.growth, "Wzrost waloryzacyjny", ZERO, Decimal(100))
    default_inflation = number(p.inflation, "Inflacja", Decimal(-50), Decimal(100))
    release = parse_date(p.release, "Zwolnienie")
    right = parse_date(p.right_date, "Ustalenie prawa")

    first_paid_month = max(month_number(release) + 1, month_number(right))
    first_year = first_paid_month // 12
    overrides = _read_overrides(p, first_year, years)

    if not result.eligible:
        return []

    legal, extra, fixed = result.pension, result.indexed_extra, result.fixed_extra
    cumulative, price_level = ZERO, Decimal(1)
    rows = []

    for year in range(first_year, first_year + years):
        growth, inflation = overrides.get(year, (default_growth, default_inflation))
        indexed_this_year = right < date(year, 3, 1)

        before_march = money(legal + extra + fixed)
        applied_rate = ZERO
        paid_in_year = ZERO
        for month in range(1, 13):
            if month == 3 and indexed_this_year:
                legal = money(legal * (1 + growth / 100))
                extra = money(extra * (1 + growth / 100))  # stałe dodatki nie rosną
                applied_rate = growth
            if year * 12 + month - 1 >= first_paid_month:
                paid_in_year += money(legal + extra + fixed)

        cumulative += paid_in_year
        price_level *= 1 + inflation / 100
        december = money(legal + extra + fixed)
        net = net_pension(december, p.pit2).net
        rows.append(ForecastRow(year, applied_rate, inflation, before_march, december, legal,
                                money(december / price_level), net, money(paid_in_year), money(cumulative)))
    return rows
