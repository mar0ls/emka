# Rozwój EMKA

Notatki dla osoby, która chce uruchomić testy, zbudować program albo wydać nową wersję. Instrukcja dla użytkowników jest w [README.md](../README.md).

## Kod

| Plik | Zawartość |
|---|---|
| `emka/engine.py` | cała logika: dobór przepisów, podstawa wymiaru, podwyższenia, netto, dorabianie, symulacja. Nie zależy od okien |
| `emka/gui.py` | okna Tk/ttk, podpowiedzi, wykres, zakładka z przepisami |
| `emka/storage.py` | profile JSON z walidacją, eksport CSV, raport Markdown |
| `emka/helptext.py` | podpowiedzi przy polach, opisy kolumn i `DISCLAIMER` (zastrzeżenie pokazywane w oknie i w raporcie) |
| `emka/PRZEPISY.md` | opis przepisów, wyświetlany też w zakładce „Przepisy” |
| `emka/assets/` | ikona (PNG, ICO, ICNS), generowana przez `tools/make_icon.py` (wymaga Pillow, sam program nie) |
| `tools/` | budowanie (`build.py`, `EMKA.spec`), obsługa wydań (`release.py`, `gitea_release.py`) |
| `tests/` | testy jednostkowe |

Program korzysta wyłącznie z biblioteki standardowej (Python 3.10+). Kwoty to `Decimal`, zaokrąglane do grosza metodą HALF_UP. W metodzie 10 lat każdy roczny wskaźnik jest zaokrąglany do 0,01 pp przed uśrednieniem.

## Testy

```sh
python3 -m unittest discover -s tests -v
```

Testy okien potrzebują sesji graficznej i Pythona z Tk, dlatego domyślnie się pomijają. Żeby je uruchomić:

```sh
EMKA_GUI_TEST=1 python3 -m unittest discover -s tests -v
```

| Plik | Co sprawdza |
|---|---|
| `test_engine.py` | wzory, granice dat (1/2.01.1999, 2012/2013), progi stażu, limity, zbieg podwyższeń, waloryzację, netto, dorabianie |
| `test_storage.py` | zapis i odczyt profili, eksporty, zachowanie przy spreparowanych plikach, obecność zastrzeżenia w README, raporcie i przepisach |
| `test_security.py` | brak importów sieciowych i dynamicznego wykonywania kodu, tylko linki `https` |
| `test_release.py` | wersja i `CHANGELOG.md`, sumy kontrolne, skrypt publikacji w Gitei, zasady w plikach workflow |
| `test_gui.py` | okna (tylko z `EMKA_GUI_TEST=1`) |

Na GitHubie testy uruchamia `.github/workflows/tests.yml` przy pushu na `main` i przy pull requestach. Na Linuksie sprawdza Pythona 3.10, 3.12 i 3.13 razem z oknami (pod `xvfb`), a na Windows i macOS Pythona 3.12 bez okien. Nic nie buduje ani nie publikuje.

## Budowanie

PyInstaller nie buduje krzyżowo, więc plik dla danego systemu trzeba zbudować na nim. Wyjątek to Linux, który można zbudować w Dockerze.

```sh
make            # lista poleceń
make mac        # EMKA.app i zip, tylko na macOS
make win        # EMKA-<wersja>-windows.exe, tylko na Windows
make linux      # EMKA-<wersja>-linux-<arch>; poza Linuksem przez Docker
make all        # wszystko, co da się zbudować na tym komputerze
make test       # testy
make clean      # usuwa build/ i dist/ (distclean także .build-venv/)
```

Bez `make` (np. na Windows) wystarczy `python tools/build.py`. Ten sam skrypt używa CI. Przy pierwszym uruchomieniu tworzy `.build-venv/` i instaluje PyInstallera w wersji z `tools/requirements-build.txt`, więc potrzebny jest internet.

Wymagany jest Python 3.10+ z Tk. Każdy zbudowany plik przechodzi `--self-test`: otwiera ukryte okno, liczy profil i sprawdza, czy dane i ikona są w środku. Na Linuksie potrzebny jest do tego wirtualny ekran (`xvfb-run`), `make linux` robi to sam.

Na Macu z Apple Silicon `make linux` buduje wersję arm64. Wersję x86_64 zbudujesz poleceniem `make linux DOCKER_PLATFORM=linux/amd64`. Plik zbudowany w Dockerze wymaga glibc nie starszego niż w obrazie Debian bookworm.

## Wydanie

Numer wersji jest tylko w `emka/__init__.py`. Czytają go `pyproject.toml`, skrypt budowania, `Makefile` i `tools/release.py`. Wersjonujemy według [SemVer](https://semver.org/lang/pl/), a 0.x oznacza program na wczesnym etapie.

1. Zmień `__version__` w `emka/__init__.py`.
2. Dopisz sekcję `## [X.Y.Z] - RRRR-MM-DD` na górze `CHANGELOG.md`. Trafi do opisu wydania.
3. Uruchom testy i zatwierdź zmiany.
4. Sprawdź tag: `python3 tools/release.py check-tag vX.Y.Z`. Polecenie weryfikuje zgodność tagu z wersją i obecność wpisu w changelogu.
5. Wypchnij tag:

   ```sh
   git tag -a vX.Y.Z -m "EMKA X.Y.Z"
   git push github vX.Y.Z      # GitHub: tu powstaje wydanie
   git push origin vX.Y.Z      # Gitea
   ```

Tagi `v*` są na GitHubie chronione: nie da się ich usunąć ani przesunąć (reguła nie ma wyjątku dla właściciela, można ją tylko wyłączyć w ustawieniach repozytorium). Błąd w wydaniu poprawia się więc kolejną wersją (np. 0.1.1 po 0.1.0). Błędne wydanie można w GitHubie oznaczyć jako wersję próbną albo usunąć, ale tag zostaje.

Co dzieje się po wypchnięciu tagu:

- **GitHub** (`.github/workflows/build.yml`). Zadanie `check` weryfikuje tag. Zadanie `build` buduje i testuje program na Windows, macOS i Linuksie. Zadanie `release` liczy sumy kontrolne programów (`SHA256SUMS`), dołącza `LICENSE` i `THIRD_PARTY_NOTICES.md` i tworzy wydanie. Ręczne uruchomienie (Actions → build → Run workflow) tylko buduje i zapisuje artefakty.
- **Gitea** (`.gitea/workflows/build.yml`). Każde zadanie dołącza własne pliki do wydania przez `tools/gitea_release.py`, więc brak runnera Windows czy macOS nie blokuje wydania Linuksa. Workflow nie był jeszcze sprawdzony na działającej instancji. Rejestrację runnerów opisuje komentarz na początku pliku.

Pliki nie są podpisane. Opisuje to README, a ryzyko [STRIDE.md](STRIDE.md).

## Aktualizacja przepisów i kwot

Reguły i kwoty urzędowe mają datę sprawdzenia w `engine.py` (`RULE_DATE`). Trzeba je odświeżać:

- progi 70% i 130% przeciętnego wynagrodzenia zmieniają się co kwartał (`INCOME_LIMIT_LOW`, `INCOME_LIMIT_HIGH`, ważne do `INCOME_LIMITS_VALID_TO`),
- kwota maksymalnego zmniejszenia i najniższa emerytura zmieniają się od marca (`MAX_REDUCTION`, `MINIMUM_PENSION`),
- po zmianie ustawy sprawdź ELI, uzupełnij testy i [WERYFIKACJA.md](WERYFIKACJA.md), a na końcu zmień `RULE_DATE`.

## Pozostałe dokumenty

- [WERYFIKACJA.md](WERYFIKACJA.md): co sprawdzono z ustawą i jakie są wyniki testów,
- [STRIDE.md](STRIDE.md): model zagrożeń,
- [CHANGELOG.md](../CHANGELOG.md): historia zmian.
