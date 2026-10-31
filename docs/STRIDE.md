# Model zagrożeń STRIDE

Dokument opisuje, co może pójść nie tak z bezpieczeństwem EMKA, co już to ogranicza i co zostaje jako ryzyko.
Dotyczy wersji 0.1.1. Przy zmianie sposobu zapisu plików, dodaniu połączeń sieciowych albo zmianie CI trzeba go przejrzeć od nowa.

## 1. Co analizujemy

EMKA to lokalny program okienkowy. Nie ma konta, serwera ani zależności zewnętrznych, a dane użytkownika zostają na jego komputerze.
Gdyby dane z profilu wyciekły, ujawniłyby zarobki, staż i sytuację emerytalną konkretnej osoby, więc poufność ma tu znaczenie.
Drugą wartością jest poprawność wyniku: błędna kwota wprowadzi użytkownika w błąd przy decyzji o odejściu ze służby.

**Aktywa**

| Aktyw | Dlaczego ważny |
|---|---|
| Profile JSON, raporty i CSV | dane finansowe i zawodowe użytkownika |
| Wzory i stałe w `engine.py` | od nich zależy poprawność każdego wyniku |
| Pliki wykonywalne z wydania | użytkownik uruchamia je u siebie z jego uprawnieniami |
| Repozytorium i CI | stąd powstają pliki wykonywalne |

**Aktorzy.** Użytkownik; osoba, która przekazuje mu plik profilu (np. znajomy, forum); inny użytkownik tego samego komputera; ktoś, kto ma dostęp do repozytorium lub CI; odbiorca pobierający program z wydania.

**Założenia.** Komputer użytkownika nie jest przejęty (złośliwe oprogramowanie z uprawnieniami użytkownika i tak przeczyta jego pliki). Użytkownik, który może zapisywać w katalogu programu, może go zmienić, więc to poza zakresem.

## 2. Przepływy danych i granice zaufania

```
                    granica 1: plik z zewnątrz
 [Plik profilu .json] ───────────────┐
                                     ▼
 [Użytkownik] ──klawiatura──▶ [GUI Tk] ──▶ [storage.py: walidacja] ──▶ [engine.py: obliczenia]
                                 │                   │
                                 │                   ▼  granica 2: system plików
                                 │          [profil .json / CSV / raport .md]
                                 │
                                 └── kliknięcie linku ──▶ [przeglądarka] ──▶ eli.gov.pl, gov.pl   (granica 3)

 [Repozytorium] ──tag v*──▶ [CI: testy, PyInstaller] ──▶ [Wydanie + SHA256SUMS] ──▶ [odbiorca]    (granica 4)
```

1. **Plik profilu z zewnątrz.** Jedyne miejsce, gdzie do programu trafiają cudze dane. Wszystko po tej granicy jest walidowane.
2. **System plików.** Program zapisuje tylko tam, gdzie wskaże użytkownik w oknie zapisu.
3. **Przeglądarka.** Program otwiera ją wyłącznie po kliknięciu linku z wbudowanego tekstu przepisów lub przycisku z adresem ELI. Nie wysyła przy tym żadnych danych użytkownika.
4. **Od repozytorium do odbiorcy.** Tu powstaje plik, któremu odbiorca zaufa na słowo.

## 3. Zagrożenia i środki zaradcze

Skróty: S podszywanie, T manipulacja, R zaprzeczenie, I ujawnienie informacji, D odmowa działania, E podniesienie uprawnień.
Kolumna „Test” wskazuje test, który pilnuje danego zabezpieczenia.

| Id | Zagrożenie | Co je ogranicza | Test | Ryzyko po zabezpieczeniu |
|---|---|---|---|---|
| S1 | Ktoś podmienia plik wykonywalny w wydaniu albo rozsyła swoją wersję jako „EMKA” | Wydanie powstaje tylko z tagu, razem z `SHA256SUMS`; kod jest otwarty, a pliki budują się z tego samego repozytorium (`tools/build.py`) | `test_release` | **Średnie**: pliki nie są podpisane, a sumę kontrolną trzeba sprawdzić samemu. Windows i macOS ostrzegą przy pierwszym uruchomieniu |
| S2 | Link w zakładce „Przepisy” prowadzi na fałszywą stronę | Tekst przepisów jest wbudowany w program, a nie pobierany. Program otwiera tylko adresy `https://`; nie ma możliwości podania własnego adresu | `test_security` | Niskie |
| S3 | Profil udaje, że pochodzi od użytkownika albo z innej wersji reguł | Plik ma numer schematu, wersję programu i datę sprawdzenia reguł; nieznany schemat jest odrzucany | `test_storage` | Niskie (profile nie są podpisywane, bo nie niosą uprawnień) |
| T1 | Spreparowany profil z błędnymi typami, `NaN`, `Infinity`, ogromnymi liczbami, nieznanymi polami | Biała lista pól, kontrola typów (`true/false` tylko jako wartości logiczne), zakresy liczb, limity rozmiaru (2 MB, 1000 pozycji na listę, 60 zmian rocznych); nazwy tylko jako krótki tekst bez znaków sterujących | `test_storage.HostileInputTests` | Niskie |
| T2 | Nazwa profilu dopisuje fałszywe nagłówki lub strukturę do raportu Markdown | Walidacja nazw przy wczytaniu; w nagłówku raportu nazwa jest sprowadzana do jednej linii; pełny profil w raporcie jest zapisany jako JSON (znaki specjalne zakodowane) | `test_report_name_cannot_inject_headings` | Niskie. Nazwa może zawierać `<` i inne znaki znaczników. Raport czytany w przeglądarce Markdown, która wykonuje surowy HTML, mógłby go pokazać |
| T3 | Formuła w arkuszu (`=HYPERLINK(...)`) przemycona przez CSV | CSV zawiera wyłącznie liczby i stałe nagłówki, nigdy tekstu użytkownika | `test_csv_contains_only_numbers...` | Niskie. Jeśli ktoś doda do CSV kolumnę tekstową, trzeba ją zabezpieczyć |
| T4 | Podsunięty profil ma zmienione progi dorabiania lub minimalną emeryturę, więc wynik jest inny, niż się wydaje | Progi są widoczne w formularzu i w raporcie; ostrzeżenie o wygasłych progach pokazuje się tylko dla wartości domyślnych | `test_engine` | **Średnie**: użytkownik może nie zauważyć obcych wartości w wczytanym pliku. Warto sprawdzić zakładkę „Netto i dorabianie” po wczytaniu cudzego profilu |
| T5 | Awaria w trakcie zapisu niszczy dotychczasowy plik | Zapis przez plik tymczasowy i zamianę; po błędzie plik tymczasowy jest usuwany | `test_failed_save_leaves_old_file...` | Niskie. CSV i raport są zapisywane bezpośrednio, ale tworzy się je od nowa, więc nic nie ginie |
| T6 | Zmiana wzorów lub stałych w kodzie, która psuje wyniki | Testy jednostkowe z granicami dat i limitów, różnicowy test starego i nowego silnika (opis w `WERYFIKACJA.md`), przegląd w repozytorium | `test_engine` | Niskie |
| T7 | Złośliwa zależność w budowaniu (PyInstaller, akcje CI, obraz Dockera) | W programie nie ma zależności zewnętrznych. PyInstaller przypięty do wersji, akcje `checkout` i `setup-python` do skrótów commitów, wydanie nie używa akcji spoza GitHuba (`gh` z runnera) | `test_release.WorkflowTests` | **Średnie**: `pip` nie sprawdza skrótów paczek, obraz `python:3.12-bookworm` nie ma przypiętego digestu, a w Gitei `upload-artifact@v3` zostaje na tagu |
| R1 | Spór o to, jaki wynik pokazał program i według jakich reguł | Raport zawiera wersję programu, datę sprawdzenia reguł, założenia i pełną konfigurację; plik profilu zapisuje wersję programu | `test_saved_file_records_program_version` | Zaakceptowane: raporty nie są podpisane i nie stanowią dowodu. Program i raport zaznaczają, że to narzędzie poglądowe, nie oficjalny kalkulator |
| R2 | Nie wiadomo, kto i co wydał | Wydanie powstaje z tagu w historii Git, log przebiegu CI zostaje w repozytorium | — | Niskie |
| I1 | Program wysyła dane użytkownika przez sieć | W kodzie nie ma modułów sieciowych ani uruchamiania procesów (test skanuje importy). Jedyne połączenie to przeglądarka otwierana po kliknięciu linku | `test_security` | Niskie |
| I2 | Profil lub raport leży na dysku jawnym tekstem | Program zapisuje tylko w wybranym miejscu, nie tworzy ukrytych kopii ani logów. Szyfrowania nie ma | — | **Średnie**: ochrona zależy od systemu (szyfrowany dysk, uprawnienia). Plik tymczasowy `.tmp` powstaje obok pliku docelowego na ułamek sekundy |
| I3 | Prawdziwe dane trafiają do repozytorium | W `examples/` są tylko dane fikcyjne, a `profiles/` jest w `.gitignore` | — | Niskie, ale zależy od uwagi autora: nie dodawaj własnych profili do `git add` |
| I4 | Wyciek sekretów z CI | Workflow używa tylko tokenu `GITHUB_TOKEN`, nie ma własnych sekretów i nie używa `pull_request_target` | `test_github_workflow_has_least_privilege` | Niskie |
| D1 | Gigantyczny lub celowo złożony plik zawiesza program | Limit 2 MB przed parsowaniem, limity list, zakresy liczb (horyzont do 60 lat, wysługa do 1200 miesięcy); sprawdzone, że skrajne wartości są odrzucane w ułamku sekundy | `test_extreme_numbers_are_rejected_quickly` | Niskie |
| D2 | Program nie startuje u odbiorcy (brak Tk, brak biblioteki) | Samokontrola `--self-test` po zbudowaniu każdego pliku; komunikat w `run.sh` i `Uruchom.bat` | build | Niskie. Windows sprawdza tylko `--self-test` w CI, nie ręczny test na pulpicie |
| D3 | Wyniki przestają być poprawne, bo wygasły progi urzędowe albo zmieniono ustawę | Daty ważności progów są w kodzie, program ostrzega po terminie; co miesiąc workflow `przepisy` sprawdza obserwowane akty w ELI i terminy kwot, a przy zmianie zakłada Issue | `test_engine`, `test_check_law` | **Średnie**: poprawki trzeba nanieść ręcznie, a kontrola widzi tylko nowe akty, nie zmiany treści bez aktu zmieniającego |
| E1 | Wczytanie pliku wykonuje obcy kod | Profil jest czytany przez `json.loads` do danych. W kodzie nie ma `eval`, `exec`, `pickle`, `subprocess` ani `os.system` | `test_security` | Niskie |
| E2 | Znaki specjalne Tcl w nazwach (`[ ]`, `$`, `{ }`) wykonują polecenia w Tk | Tekst trafia do Tk jako wartość, a nie jako skrypt | `test_tcl_special_characters...` (GUI) | Niskie |
| E3 | Ktoś z dostępem do repozytorium wypycha tag i publikuje własny program | Prawo zapisu do wydań ma tylko zadanie `release`, uruchamiane z tagu; tag musi zgadzać się z wersją i `CHANGELOG.md` | `test_release` | **Niskie** na GitHubie: zapis ma tylko właściciel, a reguła blokuje usuwanie i przesuwanie tagów `v*`. W Gitei ochrony tagów nie sprawdzono |
| E4 | Program wymaga uprawnień administratora | Nie wymaga i nie zapisuje poza wskazanymi plikami | — | Niskie |
| E5 | Workflow `przepisy` (harmonogram, prawo `issues: write`) zmienia kod albo wydaje program na podstawie danych z zewnątrz | Tylko `contents: read` i `issues: write`. Dane z API trafiają wyłącznie do treści Issue, nie do kodu ani poleceń; nie ma `git push` ani `gh release` | `test_law_watch_can_only_open_issues` | Niskie. Odpowiedź API może zawierać dowolny tytuł, który pojawi się w Issue jako tekst |

## 4. Co zostaje do zrobienia

W kolejności od najważniejszych:

1. **Ochrona tagów `v*`** jest włączona w GitHubie (reguła blokuje usuwanie i przesuwanie). Zostaje ochrona gałęzi `main` oraz ochrona tagów w Gitei.
2. **Dołączyć poświadczenie pochodzenia** plików z CI (`actions/attest-build-provenance`), dzięki czemu odbiorca zweryfikuje je poleceniem `gh attestation verify`. Wymaga publicznego repozytorium albo planu GitHub z tą funkcją.
3. **Podpisać pliki.** Windows (certyfikat Authenticode) i macOS (Apple Developer ID i notaryzacja) przestałyby ostrzegać. Kosztuje, więc na razie świadomie pominięte.
4. **Przypiąć skróty paczek** (`pip install --require-hashes`) i digest obrazu Dockera.
5. **Zabezpieczyć każdą nową kolumnę tekstową w CSV** przed formułami (poprzedzić `'` wartości zaczynające się od `=`, `+`, `-`, `@`).
6. **Zaktualizować progi dorabiania** po 30.11.2026 i kwotę maksymalną po 28.02.2027; to zagrożenie dla poprawności, nie dla bezpieczeństwa.

## 5. Jak to sprawdzono

- Przejrzano wszystkie miejsca w kodzie, które czytają i zapisują pliki, otwierają przeglądarkę lub wstawiają tekst do okien (`storage.py`, `gui.py`).
- Uruchomiono 33 spreparowane profile (złe typy, `NaN`, `Infinity`, `1e999999`, nazwa 5 MB, nazwa z nową linią, daty skrajne, listy z błędnymi polami). Wyniki z tej próby:
  - nazwa w postaci listy, liczby, tekst 5 MB lub tekst z nową linią były **przyjmowane** i trafiały do raportu. Dodano walidację;
  - błędne pola w liście podwyższeń lub dodatków kończyły się surowym `TypeError` zamiast komunikatu. Teraz jest `ValueError` z opisem;
  - plik tymczasowy zostawał na dysku po nieudanym zapisie. Teraz jest usuwany.
- Zabezpieczenia z kolumny „Test” są pilnowane automatycznie przy każdym uruchomieniu testów i w CI.

## 6. Czego ta analiza nie obejmuje

Nie obejmuje zgodności obliczeń z prawem (to osobno, w `WERYFIKACJA.md`), bezpieczeństwa systemu operacyjnego ani zaufania do Pythona, Tk i PyInstallera. Nie była też przeprowadzona przez niezależnego audytora.
