"""Sprawdza, czy zmieniły się przepisy, na których opiera się EMKA. Używa publicznego API ELI Sejmu.

    python tools/check_law.py                 # porównuje z tools/law-baseline.json i wypisuje raport
    python tools/check_law.py --report r.md   # to samo, a raport zapisuje do pliku tylko gdy coś wymaga uwagi
    python tools/check_law.py --accept        # po sprawdzeniu zmian: zapisuje bieżący stan jako nowy punkt odniesienia

Narzędzie niczego nie poprawia. Wskazuje:
- nowe akty zmieniające, wykonawcze i orzeczenia TK,
- zmianę tekstu ujednoliconego ustawy mundurowej (skrót SHA-256 pliku), także gdy nie pojawił się nowy akt zmieniający,
- nowe komunikaty w Monitorze Polskim o progach dorabiania, najniższej emeryturze i waloryzacji,
- zbliżające się terminy ważności kwot w engine.py.
Przeczytanie zmian i poprawki w kodzie zostają po stronie człowieka.
"""
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASELINE = Path(__file__).with_name("law-baseline.json")
API = "https://api.sejm.gov.pl/eli/acts/"
MAX_NEW_TITLES = 30

# Akt -> (opis, grupy powiązań, które nas interesują, czy pilnować też daty zmiany i tekstu ujednoliconego).
# Teksty FUS, PIT i ustawy zdrowotnej zmieniają się prawie co miesiąc, więc tam wystarczy lista aktów zmieniających.
WATCHED = {
    "DU/1994/214": ("Ustawa o zaopatrzeniu emerytalnym funkcjonariuszy",
                    ("Akty zmieniające", "Akty wykonawcze", "Inf. o tekście jednolitym", "Orzeczenie TK"), True),
    "DU/2005/734": ("Rozporządzenie RM o podwyższaniu emerytur funkcjonariuszy (art. 15 ust. 6)",
                    ("Akty zmieniające", "Inf. o tekście jednolitym", "Orzeczenie TK"), True),
    "DU/1998/887": ("Ustawa o emeryturach i rentach z FUS (art. 88, 104)", ("Akty zmieniające",), False),
    "DU/1991/350": ("Ustawa o podatku dochodowym od osób fizycznych (skala, kwota zmniejszająca)", ("Akty zmieniające",), False),
    "DU/2004/2135": ("Ustawa o świadczeniach opieki zdrowotnej (składka zdrowotna)", ("Akty zmieniające",), False),
}
# Fragment tytułu w Monitorze Polskim -> opis. Wyszukujemy komunikaty z bieżącego roku.
NOTICES = {
    "przychodu odpowiadających": "Progi 70% i 130% przeciętnego wynagrodzenia (komunikat Prezesa ZUS, co kwartał)",
    "najniższej emerytury": "Najniższa emerytura i kwoty maksymalnych zmniejszeń (komunikat Prezesa ZUS, od marca)",
    "waloryzacji emerytur i rent": "Wskaźnik waloryzacji emerytur (komunikat Ministra Rodziny, od marca)",
}
DEADLINE_WARNING_DAYS = 30
RULES_MAX_AGE_DAYS = 100


def _open(path):
    return urllib.request.urlopen(urllib.request.Request(API + path, headers={"User-Agent": "emka-law-check"}), timeout=60)


def fetch(path):
    """Pobiera JSON z API ELI (tylko HTTPS, limit czasu)."""
    with _open(path) as response:
        return json.load(response)


def fetch_digest(path):
    """Skrót SHA-256 pliku (np. PDF z tekstem ujednoliconym). Bajty są stabilne między pobraniami."""
    digest = hashlib.sha256()
    with _open(path) as response:
        for chunk in iter(lambda: response.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(data, groups, text_hash=None):
    """Wycina z odpowiedzi API tylko to, co porównujemy: datę zmiany, powiązane akty z datami i skrót tekstu."""
    references = data.get("references") or {}
    return {
        "changeDate": data.get("changeDate"),
        "status": data.get("status"),
        "textHash": text_hash,
        "references": {group: {item["id"]: item.get("date") for item in references.get(group, [])} for group in groups},
    }


def consolidated_text_path(eli, data):
    """Ścieżka do tekstu ujednoliconego (typ U), jeśli akt go ma."""
    for text in data.get("texts") or []:
        if text.get("type") == "U":
            return f"{eli}/text/U/{text['fileName']}"
    return None


def notice_search(query, year):
    return "search?" + urllib.parse.urlencode({"publisher": "MP", "year": year, "title": query, "limit": 50})


def take_snapshot(get=fetch, digest=fetch_digest, today=None):
    year = (today or date.today()).year
    acts = {}
    for eli, (_, groups, strict) in WATCHED.items():
        data = get(eli)
        path = consolidated_text_path(eli, data) if strict else None
        acts[eli] = snapshot(data, groups, digest(path) if path else None)
    notices = {}
    for query in NOTICES:
        items = get(notice_search(query, year)).get("items") or []
        notices[query] = {item["ELI"]: " ".join(str(item.get("title", "")).split())[:240] for item in items if "ELI" in item}
    return {"acts": acts, "notices": notices}


def differences(old, new, strict=()):
    """Zwraca listę zmian aktów: [(eli, opis, id aktu lub None)]. `strict` to akty z kontrolą daty zmiany i tekstu."""
    found = []
    for eli, current in new.items():
        before = old.get(eli)
        if before is None:
            found.append((eli, "akt nie był wcześniej obserwowany", None))
            continue
        if before["status"] != current["status"]:
            found.append((eli, f"zmienił się status: „{before['status']}” → „{current['status']}”", None))
        if eli in strict:
            if before.get("textHash") != current.get("textHash"):
                found.append((eli, "zmienił się tekst ujednolicony (inny skrót pliku PDF), być może bez nowego aktu zmieniającego", None))
            elif before["changeDate"] != current["changeDate"]:
                found.append((eli, f"zmieniła się data modyfikacji w ELI: {before['changeDate']} → {current['changeDate']}", None))
        for group, items in current["references"].items():
            was = before["references"].get(group, {})
            for act_id, effective in items.items():
                if act_id not in was:
                    found.append((eli, f"nowy wpis w grupie „{group}”: {act_id} (data: {effective or 'brak'})", act_id))
                elif was[act_id] != effective:
                    found.append((eli, f"{act_id} w grupie „{group}”: data zmieniła się z {was[act_id]} na {effective}", act_id))
            for act_id in was.keys() - items.keys():
                found.append((eli, f"zniknął wpis w grupie „{group}”: {act_id}", None))
    return found


def notice_differences(old, new):
    """Nowe komunikaty w Monitorze Polskim: [(zapytanie, opis)]."""
    found = []
    for query, items in new.items():
        for eli, title in items.items():
            if eli not in old.get(query, {}):
                found.append((query, f"nowy komunikat {eli}: {title}"))
    return found


def deadlines(today):
    """Terminy z engine.py, które mijają albo już minęły."""
    from emka import engine
    soon = today + timedelta(days=DEADLINE_WARNING_DAYS)
    items = [
        ("Progi dorabiania 70% i 130% (INCOME_LIMIT_LOW/HIGH)", engine.INCOME_LIMITS_VALID_TO),
        ("Kwota maksymalnego zmniejszenia (MAX_REDUCTION)", engine.MAX_REDUCTION_VALID_TO),
        ("Najniższa emerytura (MINIMUM_PENSION)", engine.MINIMUM_VALID_TO),
    ]
    lines = []
    for label, valid_to in items:
        if valid_to <= soon:
            verb = "wygasły" if valid_to < today else "wygasają"
            lines.append(f"{label} {verb} {valid_to:%d.%m.%Y}.")
    age = (today - date.fromisoformat(engine.RULE_DATE)).days
    if age > RULES_MAX_AGE_DAYS:
        lines.append(f"Ostatnie sprawdzenie reguł (RULE_DATE) było {age} dni temu, {engine.RULE_DATE}.")
    return lines


def titles_for(ids, get=fetch):
    """Tytuły nowych aktów, żeby raport mówił, czego dotyczą (nie więcej niż MAX_NEW_TITLES zapytań)."""
    titles = {}
    for act_id in sorted(set(ids))[:MAX_NEW_TITLES]:
        try:
            titles[act_id] = " ".join(str(get(act_id).get("title", "")).split())[:300]
        except OSError:
            titles[act_id] = ""
    return titles


def render(changes, deadline_lines, titles, today, notices=()):
    """Raport w Markdown, gotowy jako treść Issue. Pusty, gdy nic nie wymaga uwagi."""
    if not changes and not deadline_lines and not notices:
        return ""
    out = [f"# Przepisy do sprawdzenia ({today:%d.%m.%Y})", ""]
    if changes:
        out += ["## Zmiany w obserwowanych aktach", ""]
        for eli in dict.fromkeys(eli for eli, _, _ in changes):
            out += [f"**{WATCHED[eli][0]}** ([{eli}](https://eli.gov.pl/eli/{eli}/ogl/pol))", ""]
            for item_eli, text, act_id in changes:
                if item_eli == eli:
                    title = titles.get(act_id, "") if act_id else ""
                    out.append(f"- {text}" + (f": {title}" if title else ""))
            out.append("")
    if notices:
        out += ["## Nowe komunikaty w Monitorze Polskim", ""]
        for query in dict.fromkeys(query for query, _ in notices):
            out += [f"**{NOTICES[query]}**", ""] + [f"- {text}" for q, text in notices if q == query] + [""]
    if deadline_lines:
        out += ["## Terminy w kodzie", ""] + [f"- {line}" for line in deadline_lines] + [""]
    out += [
        "## Co dalej", "",
        "1. Przeczytaj zmiany w ELI i sprawdź, czy dotyczą art. 12–18h, 32, 40a–41b ustawy, rozporządzenia o podwyższeniach, "
        "art. 104 FUS, skali PIT albo składki zdrowotnej. Nowe kwoty z komunikatów wpisz w `engine.py` razem z datą ważności.",
        "2. Jeśli tak: popraw `emka/engine.py`, `emka/PRZEPISY.md`, `emka/helptext.py` i testy, a potem `RULE_DATE`.",
        "3. Zapisz nowy stan: `python3 tools/check_law.py --accept` i zatwierdź `tools/law-baseline.json`.",
        "4. Wydanie według `docs/ROZWOJ.md`.", "",
        "Ten opis wygenerował workflow `przepisy`. Nie ocenia, czy zmiana wpływa na wynik programu.",
    ]
    return "\n".join(out) + "\n"


def main(argv, get=fetch, digest=fetch_digest, today=None):
    today = today or date.today()
    accept = "--accept" in argv
    report_path = argv[argv.index("--report") + 1] if "--report" in argv and argv.index("--report") + 1 < len(argv) else None

    current = take_snapshot(get, digest, today)
    if accept:
        BASELINE.write_text(json.dumps({"checked": today.isoformat(), **current}, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
        print(f"Zapisano punkt odniesienia z {today}: {BASELINE.name}")
        return 0

    if not BASELINE.exists():
        print("Brak tools/law-baseline.json. Uruchom z --accept, żeby go utworzyć.", file=sys.stderr)
        return 2
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    strict = {eli for eli, (_, _, is_strict) in WATCHED.items() if is_strict}
    changes = differences(baseline["acts"], current["acts"], strict)
    notices = notice_differences(baseline.get("notices", {}), current["notices"])
    titles = titles_for([act_id for _, _, act_id in changes if act_id], get)
    report = render(changes, deadlines(today), titles, today, notices)
    print(report or "Bez zmian w obserwowanych aktach i bez zbliżających się terminów.")
    if report and report_path:
        Path(report_path).write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
