# Historia zmian

Format wzorowany na [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/), wersje według [SemVer](https://semver.org/lang/pl/).
Wersja 0.x oznacza program na wczesnym etapie: zakres i format plików mogą się jeszcze zmienić.

## [0.1.2] - 2026-10-31

### Zmieniono
- Zakładka „Przepisy” jest napisana od nowa: krótsze zdania, listy zamiast gęstych akapitów. Treść porównano z tekstem ustawy i rozporządzenia z ELI.
- Poprawiono opis norm dla jednostek pływających (30 dni na morzu po co najmniej 6 godzin dziennie), art. 40c (służba kontraktowa w Policji i SG), art. 6 (waloryzacja) oraz oświadczenia z art. 18h.
- Dopisano zmiany z Dz.U. 2026 poz. 26: art. 5a ustawy o FUS (sumowanie okresów, miesiąc to 30 dni) i nowy tryb orzekania o niezdolności do pracy od 1.01.2027. Wzory i limity bez zmian.

### Dodano
- Miesięczna kontrola przepisów w repozytorium (workflow `przepisy`, `tools/check_law.py`): nowe akty zmieniające, zmiana tekstu ujednoliconego ustawy, nowe komunikaty w Monitorze Polskim i zbliżające się terminy kwot. Przy zmianie zakłada Issue.

## [0.1.1] - 2026-10-31

### Naprawiono
- `SHA256SUMS` w wydaniu zawierał też `LICENSE` i `THIRD_PARTY_NOTICES.md`, więc `sha256sum -c` zgłaszał błąd, jeśli pobrano same programy. Teraz plik zawiera sumy tylko programów.

### Zmieniono
- Ochrona tagów `v*` na GitHubie jest włączona. Opis wydawania i model zagrożeń uwzględniają, że błędnego tagu nie da się usunąć.

## [0.1.0] - 2026-10-31

Pierwsze wydanie. Wcześniejsze numery robocze (do 1.3.0) nie były wydawane i nie obowiązują.

### Dodano
- Szacowanie emerytury brutto dla Policji, SG, PSP, ABW, AW, SKW, SWW, CBA, SOP, SW, SM (Straż Marszałkowska), SC i SCS według ustawy z 18.02.1994: art. 15, 15a, fakultatywny 15aa, 15d/15e, rozdział 1a i wybór art. 18h.
- Podstawa wymiaru: gotowa kwota, składniki ostatniego uposażenia albo średnia z 10 kolejnych lat (art. 18f).
- Podwyższenia roczne, strefa działań wojennych, inwalidztwo związane ze służbą, Medal im. Andrzeja Struja, limity 75/76/80/81% i najniższa emerytura.
- Własne dodatki do symulacji, liczone osobno od wyniku z ustawy.
- Emerytura netto (składka zdrowotna 9% i zaliczka na PIT) oraz skutek dorabiania w cywilnej firmie (art. 41 ustawy, art. 104 ustawy o FUS) z edytowalnymi progami.
- Symulacja waloryzacji do 60 lat z inflacją, wykres z wyborem linii, objaśnienia kolumn po najechaniu myszą.
- Porównanie scenariuszy, profile JSON, eksport CSV i raport Markdown.
- Pliki wykonywalne dla Windows, macOS i Linuksa (`make`, `tools/build.py`) oraz workflow budujący je po wypchnięciu tagu `v*`.
- Lista służb z pełnymi nazwami (np. „SM — Straż Marszałkowska”); w profilu zapisuje się skrót.
- Wczytywanie profilu odrzuca nazwy dłuższe niż 100 znaków, nie będące tekstem albo zawierające znaki sterujące.
- Raport i plik profilu zapisują numer wersji programu.
- Zastrzeżenie, że to narzędzie poglądowe, a nie oficjalny kalkulator: w oknie, w raporcie, w README i w zakładce Przepisy.
- Licencja MIT, analiza zagrożeń STRIDE (`docs/STRIDE.md`), instrukcja użytkownika w README.

### Wiadomo, że
- Wersja dla Windows jest sprawdzana tylko automatycznie przy budowaniu (test uruchomienia), nie ręcznie na komputerze z pulpitem.
- Gotowy plik dla macOS jest tylko dla Apple Silicon. Na Macu z procesorem Intel trzeba uruchomić program z kodu.
- Pliki wykonywalne nie są podpisane, więc Windows i macOS ostrzegą przy pierwszym uruchomieniu (opis w README).
- Progi dorabiania są ważne do 30.11.2026, a kwota maksymalnego zmniejszenia do 28.02.2027; potem trzeba je zaktualizować.
