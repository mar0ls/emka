# EMKA

Lokalna aplikacja okienkowa w Pythonie do szacowania emerytury brutto polskich funkcjonariuszy i symulowania jej waloryzacji. GUI: Tk/ttk. Bez zewnętrznych bibliotek, serwera, konta i wysyłania danych.

## Uruchomienie

**macOS:** dwuklik `Uruchom.command` albo `./run.sh` w katalogu projektu. Na tym komputerze skrypt wykrywa również dostarczony z Codex Python z Tk, ponieważ systemowy Python Homebrew nie ma modułu `_tkinter`.

**Windows:** Python 3.10+ z zaznaczoną obsługą Tcl/Tk i launcherem `py`; dwuklik `Uruchom.bat`.

**Linux:** Python 3.10+ z Tk i sesją graficzną, następnie `./run.sh`. W wielu dystrybucjach Tk jest osobnym pakietem systemowym.

Ręcznie: `python3 -m emka`. Sprawdzenie Tk: `python3 -m tkinter`. Wskazanie konkretnego interpretera: `EMKA_PYTHON=/pełna/ścieżka/python3 ./run.sh`.

Opcjonalna instalacja jako pakiet: `python3 -m pip install .`, następnie `emka`. Tk musi być dostępny w używanym interpreterze. Program startuje z **przykładowymi danymi**, które należy zastąpić swoimi.

## Możliwości

- Policja, SG, PSP, ABW, AW, SKW, SWW, CBA, SOP, SW, SM, SC i SCS.
- Wybór reguł według pierwszego właściwego przyjęcia; art. 15, 15a, fakultatywny 15aa, 15d/15e, rozdział 1a oraz wybór art. 18h.
- Pełne miesiące wysługi, okresy cywilne i odrębny warunek 25 lat do art. 15aa.
- Gotowa podstawa, składniki ostatniego uposażenia albo wskaźnikowa podstawa z 10 kolejnych lat.
- Potwierdzone podwyższenia roczne, strefa wojny, inwalidztwo związane ze służbą i Medal im. Andrzeja Struja; właściwe limity 75/76/80/81%.
- Rozliczanie zbiegu podwyższeń w tych samych miesiącach; brak automatycznego sumowania.
- Własne fakultatywne dodatki w pp podstawy, % emerytury lub zł miesięcznie; włączenie/wyłączenie i waloryzowanie osobno dla każdej pozycji.
- Symulacja do 60 lat, domyślna waloryzacja i inflacja oraz różne wartości w wybranych latach; wykres, kwoty realne, suma roczna z marcową waloryzacją i suma narastająca.
- Porównanie niezależnych kopii scenariuszy, profile JSON, CSV otwierane z polskimi separatorami i raport Markdown z pełnymi danymi oraz założeniami.
- **Emerytura netto:** składka zdrowotna 9% i zaliczka na PIT (12%/32%, z kwotą zmniejszającą 300 zł miesięcznie albo bez niej); netto także w symulacji, CSV i raporcie.
- **Dorabianie w cywilnej firmie:** o ile zmniejszy się emerytura mundurowa przy danym przychodzie brutto (art. 41 ustawy i art. 104 ustawy o FUS): do 70% przeciętnego wynagrodzenia bez zmian, 70–130% o kwotę przekroczenia (nie więcej niż kwota maksymalna i 25% emerytury), powyżej 130% o 25%; emerytura równa 75% podstawy nie jest zmniejszana. Progi są edytowalne, bo ZUS zmienia je co kwartał.
- Reguły i źródła dostępne bezpośrednio w zakładce „Przepisy”.
- Chmurki przy polach, etykietach i przyciskach ⓘ: najedź myszą albo naciśnij F1 w aktywnym polu. Pomoc jest również w oknach dodawania pozycji.
- Checkbox systemu: odznaczony = właściwe przyjęcie przed 1.01.2013 (15 lat / 40%); zaznaczony = od 1.01.2013 (25 lat / 60%) albo wybór art. 18h dla wcześniejszego przyjęcia. Zmiana daty automatycznie podpowiada właściwy system; program blokuje sprzeczne wybory.
- Informacja o właściwych przepisach aktualizuje się po zmianie służby i systemu. W porównaniu każdy scenariusz zachowuje własną służbę, a zaznaczenie wiersza wyświetla jego reguły, podstawę wymiaru, organ i uwagi szczególne. Te informacje zawiera też raport.

## Jak używać

1. **Dane:** wybierz służbę, podaj daty (RRRR-MM-DD albo DD.MM.RRRR) i pełne miesiące z dokumentacji. Pod polem wysługi program pokazuje, ile pełnych miesięcy mieści się między datą przyjęcia a zwolnieniem; wpisanie większej liczby jest odrzucane. Pierwsze właściwe przyjęcie uwzględnia wcześniejszą służbę i wyjątki ustawowe. `auto` nie rozpoznaje samodzielnie historii personalnej.
2. **Podstawa:** wybierz właściwy tryb. Wpisanie gotowej kwoty nie zastępuje ustalenia jej zgodnie z art. 5/18f. Dla SM/SC/SCS i rozdziału 1a obowiązuje metoda 10 lat.
3. **Podwyższenia:** dodaj zaliczone okresy. Miesiące początku i końca są wliczane; strefa wojny obejmuje rozpoczęty miesiąc. Potwierdź, że jednostka zaliczyła okres po weryfikacji wymaganych norm.
4. **Dodatki:** dodaj własne pozycje wariantu. Pokazywane są osobno od świadczenia obliczonego według reguł ustawy.
5. **Symulacja:** ustaw wzrost w procentach, np. `4`, i inflację, np. `2,5`. Domyślne 4% i 2,5% są wyłącznie przykładem. Kliknij „Oblicz emeryturę” lub F5. Roczne wyjątki muszą mieścić się w horyzoncie.
6. Dodaj wynik do porównania, zmień dane, dodaj następny. Dwuklik wariantu przywraca jego konfigurację. Porównanie trwa przez bieżącą sesję; **zapisuj poszczególne profile JSON**, aby zachować je na później.

Zmiana danych unieważnia poprzedni wynik, aby uniknąć eksportu nieaktualnych obliczeń. Wszystkie eksporty przeliczają profil przed zapisem. Ctrl/Cmd+S otwiera zapis profilu. JSON zapisuje całą konfigurację; traktuj go jak własny dokument finansowy. W katalogu `examples/` znajdują się fikcyjne profile do wypróbowania.

## Przepisy i ograniczenia

Źródła sprawdzono **29.10.2026**. Przed implementacją przygotowano [szczegółową analizę](emka/PRZEPISY.md) z artykułami, warunkami, wyjątkami i odnośnikami do ELI oraz ZER MSWiA. Nie jest to kalkulator decyzji administracyjnych. Wynik dotyczy reguł wysokości świadczenia przy zadeklarowanych danych, a etykieta stażu oznacza wyłącznie spełnienie progu miesięcy.

Program przyjmuje wysługę już potwierdzoną: nie kwalifikuje zdarzeń, norm rocznych ani okresów cywilnych/KAS. Nie odtwarza historycznych emerytur sprzed 2026 r. Przyszłe odejścia i waloryzacje zakładają niezmienność opisanych reguł. Nietypowe SC/SCS, mieszane służby w roku i art. 15c wymagają indywidualnej analizy; odpowiednie przypadki blokują standardowy wzór. Obliczenia podstawowe są brutto; netto obejmuje wyłącznie podatek i składkę zdrowotną od samej emerytury (bez innych dochodów). Program nie uwzględnia rent, 13./14. świadczenia, potrąceń ani zbiegu wypłat. Dorabianie liczy skutek miesięczny przy stałym przychodzie, a rozliczenie następuje w rzeczywistości po zakończeniu roku.

Wypłaty roczne: od następnego pełnego miesiąca po zwolnieniu, nie wcześniej niż w miesiącu ustalenia prawa. Pominięto niepełne miesiące i wyrównania. Wartości realne dotyczą grudnia w cenach początku pierwszego roku symulacji. 1978,49 zł to minimum od marca 2026 do lutego 2027; dla innych dat trzeba podać właściwą kwotę. Stopy przyszłej waloryzacji są założeniem użytkownika.

## Testy i rozwój

`python3 -m unittest discover -s tests -v`

Testy komponentów GUI, wymagające działającej sesji graficznej i Tk:

`EMKA_GUI_TEST=1 python3 -m unittest discover -s tests -v`

Obliczenia pieniężne korzystają z `Decimal`, zaokrąglenia do grosza metodą HALF_UP. Każdy stosunek roczny w metodzie 10 lat jest osobno zaokrąglany do 0,01 punktu procentowego przed obliczeniem średniej. Pozostałe przyrosty są liczone w pełnych miesiącach. Testy obejmują m.in. granice dat i stażu, różnice systemów, limity, zbieg podwyższeń, marcową waloryzację, profile i eksporty.

Struktura: `emka/engine.py` — reguły; `emka/gui.py` — okna; `emka/storage.py` — profile i raporty; `emka/assets/` — ikona (PNG, ICO, ICNS), odtwarzana skryptem `tools/make_icon.py` (wymaga Pillow, sam program nie); `emka/PRZEPISY.md` — analiza przepisów (ten sam plik jest pokazywany w zakładce „Przepisy”, więc nie ma drugiej kopii do synchronizacji); `docs/WERYFIKACJA.md` — wyniki weryfikacji. Przed zmianą wersji reguł trzeba ponownie zweryfikować źródła i daty wejścia w życie oraz uzupełnić testy.
