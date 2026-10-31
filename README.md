# EMKA

[![build](https://github.com/mar0ls/emka/actions/workflows/build.yml/badge.svg)](https://github.com/mar0ls/emka/actions/workflows/build.yml)
[![tests](https://github.com/mar0ls/emka/actions/workflows/tests.yml/badge.svg)](https://github.com/mar0ls/emka/actions/workflows/tests.yml)
[![wydanie](https://img.shields.io/github/v/release/mar0ls/emka?include_prereleases&label=wydanie)](https://github.com/mar0ls/emka/releases)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![platformy](https://img.shields.io/badge/platformy-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
[![licencja MIT](https://img.shields.io/badge/licencja-MIT-green)](LICENSE)

EMKA to program na komputer, który szacuje emeryturę funkcjonariusza służb mundurowych (Policja, Straż Graniczna, PSP, ABW, AW, SKW, SWW, CBA, SOP, Służba Więzienna, Straż Marszałkowska, Służba Celna i Celno-Skarbowa) według ustawy z 18 lutego 1994 r. Pokazuje też, ile z tej kwoty zostanie po podatku i składce zdrowotnej, jak emerytura będzie rosła przez kolejne lata i o ile zmaleje, jeśli po odejściu ze służby będziesz dorabiać w cywilnej firmie.

Wszystko dzieje się na Twoim komputerze. Program nie ma konta, nie łączy się z internetem i niczego nie wysyła.

> **To narzędzie poglądowe, a nie oficjalny kalkulator.** Autor nie jest związany z MSWiA, ZER MSWiA, ZUS ani żadną ze służb, a program nie jest przez nie sprawdzany ani polecany. Wynik jest szacunkiem, nie decyzją organu emerytalnego ani poradą prawną. Program przyjmuje dane, które mu podasz, i nie sprawdza ich w dokumentach. O prawie do emerytury i jej wysokości decyduje wyłącznie organ emerytalny (dla większości służb ZER MSWiA). Przed decyzją o odejściu ze służby poproś go o oficjalne wyliczenie.

## Spis treści

1. [Pobranie i uruchomienie](#pobranie-i-uruchomienie)
2. [Instrukcja krok po kroku](#instrukcja-krok-po-kroku)
3. [Jak czytać wynik](#jak-czytać-wynik)
4. [Czego program nie robi](#czego-program-nie-robi)
5. [Najczęstsze problemy](#najczęstsze-problemy)
6. [Dla programistów, licencja](#dla-programistów-i-licencja)

## Pobranie i uruchomienie

### Gotowy program

Wejdź na stronę Releases repozytorium ([github.com/mar0ls/emka](https://github.com/mar0ls/emka/releases)) i pobierz plik dla swojego systemu. Python nie jest potrzebny.

| System | Plik | Jak uruchomić |
|---|---|---|
| Windows 10/11 (64-bitowy) | `EMKA-<wersja>-windows.exe` | Dwuklik. Przy pierwszym uruchomieniu Windows może pokazać „System Windows ochronił ten komputer”: kliknij Więcej informacji, potem Uruchom mimo to. |
| macOS (Apple Silicon) | `EMKA-<wersja>-macos-arm64.zip` | Rozpakuj i przeciągnij `EMKA.app` do Programów. Przy pierwszym uruchomieniu kliknij aplikację prawym przyciskiem i wybierz Otwórz. Jeśli system i tak odmawia: Ustawienia systemowe → Prywatność i ochrona → Otwórz mimo to. |
| Linux (x86_64, z graficznym pulpitem) | `EMKA-<wersja>-linux-x86_64` | W terminalu: `chmod +x EMKA-*-linux-x86_64`, potem `./EMKA-*-linux-x86_64`. |

Pliki nie są podpisane cyfrowo (certyfikaty kosztują), dlatego systemy ostrzegają. Programy antywirusowe mogą też czasem zgłosić fałszywy alarm przy plikach z PyInstallera. Jeśli wolisz mieć pewność, że plik jest taki, jaki wyszedł z budowania, sprawdź jego sumę kontrolną:

- Windows (PowerShell): `Get-FileHash .\EMKA-0.1.2-windows.exe -Algorithm SHA256`
- macOS: `shasum -a 256 EMKA-0.1.2-macos-arm64.zip`
- Linux: `sha256sum EMKA-0.1.2-linux-x86_64`

Wynik musi być taki sam jak odpowiednia linia w pliku `SHA256SUMS` dołączonym do wydania (zawiera sumy samych programów). Wersja dla Windows jest sprawdzana tylko automatycznie przy budowaniu (test uruchomienia), nie na prawdziwym komputerze, więc jeśli coś nie działa, daj znać. Dla Maców z procesorem Intel nie ma gotowego pliku: uruchom program z kodu źródłowego.

### Z kodu źródłowego

Potrzebujesz Pythona 3.10 lub nowszego z Tk (okna). Sprawdzisz to poleceniem `python3 -m tkinter`: jeśli pojawi się małe okienko, wszystko jest w porządku.

- macOS: dwuklik `Uruchom.command` albo `./run.sh`. Python z Homebrew często nie ma Tk; wtedy zainstaluj Pythona z python.org.
- Windows: dwuklik `Uruchom.bat` (wymaga Pythona z launcherem `py` i Tcl/Tk).
- Linux: `./run.sh`. Tk bywa osobnym pakietem, np. `sudo apt install python3-tk`.
- Ręcznie: `python3 -m emka`. Konkretny interpreter wskażesz zmienną: `EMKA_PYTHON=/pełna/ścieżka/python3 ./run.sh`.

## Instrukcja krok po kroku

Program startuje z **przykładowymi danymi**. Zanim zaufasz jakiejkolwiek liczbie, zamień je na swoje. W katalogu `examples/` są trzy gotowe fikcyjne profile do obejrzenia (przycisk Otwórz profil).

### Co przygotować

- datę pierwszego przyjęcia do służby i datę zwolnienia (planowanego odejścia),
- wysługę emerytalną w pełnych miesiącach z dokumentacji jednostki,
- ostatnie uposażenie (zasadnicze, stałe dodatki, nagroda roczna) albo już policzoną podstawę wymiaru,
- jeśli dotyczy: okresy z podwyższeniem (praca w warunkach szczególnych), okresy cywilne przed służbą i po niej.

Zakładki w oknie wypełniasz po kolei od lewej. Wynik jest zawsze widoczny po prawej stronie. Przy każdym polu jest ikonka ⓘ: najedź na nią myszą albo naciśnij F1 w polu, a pokaże się wyjaśnienie.

### Zakładka 1: Dane

1. Wpisz nazwę profilu (np. „Ja, odejście w 2027”).
2. Wybierz służbę z listy. Skróty są rozwinięte, np. SM to Straż Marszałkowska (Straż Miejska nie podlega tej ustawie).
3. Wpisz daty jako `RRRR-MM-DD` albo `DD.MM.RRRR`: pierwsze przyjęcie, zwolnienie i datę ustalenia prawa do emerytury (zwykle dzień po zwolnieniu).
   - Pierwsze przyjęcie to pierwsze właściwe przyjęcie do służby, razem z wcześniejszą służbą, którą ustawa zalicza. Nie wpisuj daty ostatniego powrotu do służby.
4. Program sam podpowiada system emerytalny: do końca 2012 r. stary (próg 15 lat, 40% podstawy), od 2013 r. nowy (próg 25 lat, 60%). Pole „Sposób ustalenia emerytury” zostaw na `auto`, chyba że świadomie wybierasz art. 15aa albo 18h.
5. Wpisz łączną wysługę w miesiącach. Pod polem zobaczysz, ile pełnych miesięcy mieści się między przyjęciem a zwolnieniem. Większa liczba zostanie odrzucona.
6. Jeśli miałeś okresy cywilne (składkowe lub nieskładkowe) przed służbą albo chcesz doliczyć okres po służbie, wpisz miesiące w sekcji „Okresy cywilne”.
7. Zaznacz pola w sekcji „Przypadki wymagające odrębnej analizy” tylko wtedy, gdy Cię dotyczą. Program nie policzy wtedy emerytury, tylko pokaże komunikat, bo takie sprawy trzeba rozstrzygnąć indywidualnie.

### Zakładka 2: Podstawa

Wybierz sposób ustalenia podstawy wymiaru:

- gotowa podstawa: wpisujesz kwotę, którą już masz z jednostki lub z własnych wyliczeń,
- składniki uposażenia: program liczy z ostatniego uposażenia, stałych dodatków i nagrody rocznej,
- 10 kolejnych lat: średnia z dziesięciu lat. Obowiązuje w nowym systemie oraz w SM, SC i SCS. Wpisz urzędowe przeciętne uposażenie na dzień zwolnienia, a w tabeli dodaj dziesięć lat: dla każdego swoje roczne uposażenie i urzędowe roczne przeciętne uposażenie.

Na dole możesz zmienić najniższą emeryturę. Domyślna kwota (1978,49 zł) obowiązuje od marca 2026 do lutego 2027.

### Zakładka 3: Podwyższenia

Zaznacz inwalidztwo związane ze służbą (+15 pp) albo Medal im. Struja (+1 pp), jeśli dotyczy. Okresy szczególnej służby dodaj przyciskiem + Dodaj, podając miesiące początku i końca w formacie `RRRR-MM`. Każdy okres trzeba potwierdzić: zaznaczasz, że jednostka go zaliczyła po sprawdzeniu wymaganych norm. Niepotwierdzony okres nie jest liczony.

### Zakładka 4: Dodatki

Tu możesz sprawdzić własny wariant, np. „co jeśli dostanę dodatkowe 2 pp” albo „stały dodatek 150 zł”. Te pozycje pokazują się obok wyniku z ustawy i nigdy go nie zmieniają.

### Zakładka 5: Netto i dorabianie

- Zaznacz, czy rozliczasz emeryturę z kwotą zmniejszającą podatek (300 zł miesięcznie). Dotyczy to osób, które złożyły oświadczenie PIT-2 u płatnika emerytury.
- Wpisz miesięczny przychód brutto z pracy w cywilnej firmie. Program pokaże, o ile zmniejszy się emerytura i ile zostanie na rękę. Tabela niżej pokazuje, jak to wygląda przy różnych przychodach.
- Progi 70% i 130% przeciętnego wynagrodzenia oraz kwota maksymalnego zmniejszenia zmieniają się co kwartał. Wpisane domyślnie obowiązują do 30.11.2026. Po tej dacie sprawdź aktualne wartości (komunikat Prezesa ZUS w Monitorze Polskim) i wpisz je w polach.

### Zakładka 6: Symulacja

Wpisz horyzont (liczba lat), przewidywany wzrost waloryzacji (np. `4`) i inflację (np. `2,5`). Domyślne wartości to tylko przykład. Dla wybranych lat możesz podać inne stopy w tabeli. Pod tabelą jest wykres. Pola nad nim włączają i wyłączają linie: „Wariant (mies.)”, „Ustawa (mies.)”, „Wartość realna” i „Netto (mies.)”. Najedź na nagłówek kolumny tabeli, żeby zobaczyć, co oznacza.

### Obliczenie i zapis

1. Kliknij Oblicz emeryturę (albo F5). Po każdej zmianie danych wynik się unieważnia i trzeba policzyć ponownie.
2. Dodaj wynik do porównania zapisuje scenariusz na zakładce „Porównanie”. Zmień dane, policz i dodaj następny, a potem porównaj. Dwuklik na scenariuszu przywraca jego dane. Porównanie istnieje tylko do zamknięcia programu.
3. Zapisz profil (Ctrl/Cmd+S) zapisuje wszystkie dane do pliku `.json`, który otworzysz później przyciskiem Otwórz profil. To Twoje dane finansowe, więc przechowuj plik tak ostrożnie jak inne dokumenty. Wczytując plik od kogoś innego, sprawdź progi na zakładce 5.
4. Eksport CSV zapisuje symulację do arkusza (separator `;`, polskie przecinki, otwiera się w Excelu).
5. Raport zapisuje plik Markdown z wynikiem, założeniami i pełną konfiguracją. Dobrze nadaje się do archiwum albo do pokazania doradcy.

## Jak czytać wynik

Panel po prawej pokazuje:

- Kwota brutto, czyli emerytura według reguł ustawy, miesięcznie.
- Netto, czyli po składce zdrowotnej 9% i zaliczce na PIT, liczone tylko od samej emerytury.
- System (np. „15aa” albo „rozdział 1a”) i podstawę wymiaru z procentem, który do niej zastosowano.
- Wariant z własnymi dodatkami, jeśli jakieś dodałeś.
- Poniżej listę składników procentowych i założeń. Warto ją przeczytać, bo tam program zapisuje, co przyjął za pewnik.
- Na czerwono skutek dorabiania, jeśli wpisałeś przychód z pracy. Ostrzeżenia o progach, które mogły wygasnąć, albo o skoku zmniejszenia po przekroczeniu 130% pokazuje zakładka 5.

W symulacji kolumny oznaczają kwoty z grudnia danego roku, chyba że nazwa mówi inaczej. „Wartość realna” to kwota w cenach początku pierwszego roku symulacji, czyli po uwzględnieniu inflacji.

## Czego program nie robi

- Nie sprawdza Twoich dokumentów i nie ustala prawa do emerytury. Spełnienie progu stażu to tylko spełnienie progu miesięcy.
- Nie kwalifikuje zdarzeń służby ani norm rocznych dla podwyższeń. Wpisujesz okresy, które jednostka już zaliczyła.
- Nie liczy spraw wymagających indywidualnej analizy: art. 15c (służba w organach bezpieczeństwa PRL), wyłączeń z art. 10, mieszanej służby w jednym roku, części przypadków SC i SCS.
- Nie uwzględnia rent, 13. i 14. emerytury, potrąceń, zbiegu wypłat ani innych dochodów poza samą emeryturą.
- Nie odtwarza emerytur przyznanych przed 2026 r. i nie przewiduje zmian prawa. Prognoza zakłada, że reguły się nie zmienią.
- Dorabianie liczy dla stałego miesięcznego przychodu. W rzeczywistości rozliczenie następuje po zakończeniu roku.

Pełny opis przepisów, które program stosuje, jest w zakładce Przepisy (to samo w pliku [emka/PRZEPISY.md](emka/PRZEPISY.md)). Wyniki sprawdzenia programu z ustawą opisuje [docs/WERYFIKACJA.md](docs/WERYFIKACJA.md).

## Najczęstsze problemy

| Problem | Co zrobić |
|---|---|
| „Wysługa jest dłuższa niż czas od pierwszego przyjęcia do zwolnienia” | Popraw daty albo liczbę miesięcy. Okresy równorzędne sprzed przyjęcia uwzględnij, wpisując wcześniejszą datę pierwszego przyjęcia. |
| W panelu pojawia się „Brak stażu” | Liczba miesięcy jest mniejsza niż próg (15 lat w starym systemie, 25 w nowym). Emerytura nie przysługuje. |
| „Dane zmienione. Oblicz ponownie.” | To normalne. Kliknij Oblicz emeryturę albo naciśnij F5. |
| Okno z komunikatem „Przypadek wymaga indywidualnego rozstrzygnięcia” | Zaznaczyłeś jedno z pól w sekcji „Przypadki wymagające odrębnej analizy” na zakładce 1. Program celowo nie liczy takich spraw; rozstrzyga je organ emerytalny. |
| Nie otwiera się profil | Plik musi pochodzić z EMKA (format `.json` z tej aplikacji), mieć mniej niż 2 MB i poprawne wartości. Komunikat podaje, które pole jest błędne. |
| Przy uruchomieniu z kodu: brak modułu `_tkinter` | Twój Python nie ma Tk. Zainstaluj Pythona z obsługą Tcl/Tk (python.org) albo pakiet `python3-tk`. |
| Windows blokuje plik `.exe` | Patrz [Gotowy program](#gotowy-program): „Więcej informacji”, potem „Uruchom mimo to”. |

## Dla programistów i licencja

Budowanie plików wykonywalnych, uruchamianie testów, struktura kodu i procedura wydania są opisane w [docs/ROZWOJ.md](docs/ROZWOJ.md). Model zagrożeń (STRIDE) jest w [docs/STRIDE.md](docs/STRIDE.md), a historia zmian w [CHANGELOG.md](CHANGELOG.md).

Autor: [mar0ls](https://github.com/mar0ls). Program jest udostępniony na licencji MIT (plik [LICENSE](LICENSE)): możesz go używać, kopiować i zmieniać za darmo, ale bez żadnej gwarancji. Pliki wykonywalne zawierają dodatkowo Pythona, Tcl/Tk i program ładujący PyInstallera; ich licencje wymienia [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
