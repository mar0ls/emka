# Rozwój EMKA

Ten plik jest dla osób, które chcą zbudować program, uruchomić testy albo wydać nową wersję. Instrukcja użytkownika jest w [README.md](../README.md).

## Struktura kodu

| Plik | Co robi |
|---|---|
| `emka/engine.py` | cała logika: wybór przepisów, podstawa wymiaru, podwyższenia, netto, dorabianie, symulacja. Nie zna okien |
| `emka/gui.py` | okna Tk/ttk, tooltipy, wykres, zakładka z przepisami |
| `emka/storage.py` | zapis i odczyt profili JSON z walidacją, eksport CSV, raport Markdown |
| `emka/helptext.py` | teksty podpowiedzi przy polach i opisy kolumn |
| `emka/PRZEPISY.md` | opis przepisów; ten sam plik pokazuje zakładka „Przepisy” |
| `emka/assets/` | ikona (PNG, ICO, ICNS), odtwarzana skryptem `tools/make_icon.py` (wymaga Pillow, sam program nie) |
| `tools/` | budowanie (`build.py`, `EMKA.spec`), pomocnik wydań (`release.py`), publikacja w Gitei (`gitea_release.py`) |
| `tests/` | testy jednostkowe |

Program używa tylko biblioteki standardowej Pythona 3.10+. Kwoty liczymy na `Decimal` z zaokrągleniem do grosza metodą HALF_UP. Każdy roczny wskaźnik w metodzie 10 lat jest osobno zaokrąglany do 0,01 punktu procentowego, zanim policzymy średnią.

## Testy

```sh
python3 -m unittest discover -s tests -v
```

Testy okien potrzebują sesji graficznej i Pythona z Tk, więc domyślnie są pomijane. Żeby je włączyć:

```sh
EMKA_GUI_TEST=1 python3 -m unittest discover -s tests -v
```

Co jest sprawdzane:

- `test_engine.py`: wzory, granice dat (1/2.01.1999, 2012/2013), progi stażu, limity, zbieg podwyższeń, waloryzacja, netto, dorabianie.
- `test_storage.py`: zapis i odczyt profili, eksporty oraz zachowanie przy spreparowanych plikach.
- `test_security.py`: kod nie importuje modułów sieciowych ani nie wykonuje obcego kodu.
- `test_release.py`: wersja, `CHANGELOG.md`, sumy kontrolne, skrypt publikacji w Gitei i zasady w plikach workflow.
- `test_gui.py`: okna (tylko z `EMKA_GUI_TEST=1`).

Zastrzeżenie, że to narzędzie poglądowe, mieszka w `DISCLAIMER` w `emka/helptext.py` (okno i raport). Testy pilnują, żeby było też w README i w `PRZEPISY.md`.

## Budowanie programu

PyInstaller nie buduje krzyżowo: plik dla danego systemu trzeba zbudować na tym systemie. Wyjątkiem jest Linux, który da się zbudować w Dockerze na innym systemie.

```sh
make            # pomoc
make mac        # EMKA.app i zip, tylko na macOS
make win        # EMKA-<wersja>-windows.exe, tylko na Windows
make linux      # EMKA-<wersja>-linux-<arch>; poza Linuksem przez Docker
make all        # wszystko, co da się zbudować na tym komputerze
make test       # testy
make clean      # usuwa build/ i dist/ (distclean usuwa też .build-venv/)
```

Bez `make` (np. na Windows): `python tools/build.py`. Ten sam skrypt jest używany w `make` i w CI. Przy pierwszym uruchomieniu tworzy środowisko `.build-venv/` z PyInstallerem w wersji z `tools/requirements-build.txt`, więc potrzebuje internetu.

Wymagany jest Python 3.10+ z Tk. Każdy zbudowany plik przechodzi `--self-test`: otwiera ukryte okno, liczy profil i sprawdza, że dane i ikona są w środku. Na Linuksie trzeba do tego wirtualnego ekranu (`xvfb-run`); `make linux` robi to sam.

Na Macu z Apple Silicon `make linux` buduje wersję arm64. Dla x86_64: `make linux DOCKER_PLATFORM=linux/amd64`. Program z Dockera wymaga glibc nie starszego niż w obrazie Debian bookworm.

## Wydanie nowej wersji

Numer wersji jest tylko w `emka/__init__.py`. Czytają go `pyproject.toml`, budowanie, `Makefile` i `tools/release.py`. Stosujemy [SemVer](https://semver.org/lang/pl/): 0.x oznacza program we wczesnej fazie.

1. Zmień `__version__` w `emka/__init__.py`.
2. Dopisz sekcję `## [X.Y.Z] - RRRR-MM-DD` na górze `CHANGELOG.md`. Jej treść trafi do opisu wydania.
3. Uruchom testy i zatwierdź zmiany.
4. Sprawdź lokalnie: `python3 tools/release.py check-tag vX.Y.Z` (sprawdza zgodność tagu z wersją i obecność wpisu w changelogu).
5. Wypchnij tag:

   ```sh
   git tag vX.Y.Z
   git push origin vX.Y.Z      # Gitea
   git push github vX.Y.Z      # GitHub (tu powstanie pełne wydanie)
   ```

Co dzieje się dalej:

- **Testy** (`.github/workflows/tests.yml`): przy pushu na `main` i pull requestach uruchamiają testy na Linuksie (Python 3.10, 3.12, 3.13, razem z oknami pod `xvfb`) oraz na Windows i macOS (Python 3.12, bez testów okien). Nic nie budują ani nie publikują.
- **GitHub** (`.github/workflows/build.yml`): zadanie `check` weryfikuje tag, zadanie `build` buduje i testuje program na Windows, macOS i Linuksie, a zadanie `release` tworzy wydanie z trzema plikami, `SHA256SUMS`, `LICENSE` i `THIRD_PARTY_NOTICES.md`. Ręczne uruchomienie (Actions → build → Run workflow) tylko buduje i zapisuje artefakty, niczego nie publikuje.
- **Gitea** (`.gitea/workflows/build.yml`): każde zadanie dołącza własne pliki do wydania (`tools/gitea_release.py`). Brak runnera Windows lub macOS nie blokuje wydania Linuksa. Workflow nie był jeszcze uruchamiany na prawdziwej instancji. Opis rejestracji runnerów jest w komentarzu na początku pliku.

Pliki nie są podpisane, co opisuje README. Jeśli wydanie się nie powiedzie, popraw przyczynę, usuń błędny tag (`git tag -d vX.Y.Z` oraz `git push origin :refs/tags/vX.Y.Z`) i wydanie, a potem wypchnij tag jeszcze raz albo podnieś wersję o jeden numer.

## Aktualizacja przepisów i kwot

Reguły i kwoty urzędowe mają datę sprawdzenia w `engine.py` (`RULE_DATE`). Co jakiś czas trzeba je odświeżyć:

- progi 70% i 130% przeciętnego wynagrodzenia zmieniają się co kwartał (`INCOME_LIMIT_LOW/HIGH`, ważne do `INCOME_LIMITS_VALID_TO`),
- kwota maksymalnego zmniejszenia emerytury i najniższa emerytura zmieniają się od marca (`MAX_REDUCTION`, `MINIMUM_PENSION`),
- po każdej zmianie ustawy sprawdź ELI, uzupełnij testy i [WERYFIKACJA.md](WERYFIKACJA.md), potem zmień `RULE_DATE`.

## Dokumenty

- [WERYFIKACJA.md](WERYFIKACJA.md): zgodność obliczeń z ustawą i wyniki testów.
- [STRIDE.md](STRIDE.md): model zagrożeń.
- [../CHANGELOG.md](../CHANGELOG.md): historia zmian.
