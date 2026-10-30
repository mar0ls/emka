"""Treści pomocy kontekstowej dla pól kalkulatora."""
HELP = {
    "name": "Dowolna nazwa, np. „PSP — odejście w 2028”. Pojawi się w raporcie i porównaniu. Nie musisz wpisywać imienia ani danych osobowych.",
    "service": "Wybierz służbę, z której przechodzisz na emeryturę. Poniżej od razu zmienią się informacje o podstawie wymiaru, właściwym organie i szczególnych warunkach. Wcześniejsza służba wpływa też na datę pierwszego przyjęcia.",
    "first_entry": "Data (RRRR-MM-DD lub DD.MM.RRRR) pierwszego właściwego przyjęcia. Uwzględnij wyjątki art. 18a ust. 2, np. wcześniejszą zawodową służbę wojskową lub kandydacką przed 2013 r. Nie wpisuj wyłącznie daty ostatniego powrotu. Zmiana tej daty ustawi przełącznik systemu według granicy 1.01.2013.",
    "release": "Data zakończenia służby albo planowanego odejścia (RRRR-MM-DD lub DD.MM.RRRR). Kalkulator stosuje reguły sprawdzone w 2026 r. Dla przyszłości zakłada ich niezmienność. Suma roczna wypłat zaczyna się od następnego pełnego miesiąca po tej dacie.",
    "right_date": "Data ustalenia prawa do świadczenia, nie data pierwszego przelewu. Przy planowaniu wpisz zakładaną datę. Ustalenie prawa przed 1 marca pozwala uwzględnić marcową waloryzację w tym roku; 1 marca lub później — od kolejnego roku.",
    "regime": "auto: wariant wynikający z daty i wybranego systemu. 15aa: fakultatywny wariant dla właściwych przyjęć 2.01.1999–30.09.2003. 18h: wybór zasad 25 lat / 60% dla wcześniejszych przyjęć. Zmiany wyboru są sprawdzane pod kątem zgodności z datą.",
    "new_system": "Zaznaczone: rozdział 1a — 60% za 25 lat, dalszy rok +3 pp, podstawa z 10 lat. Dla wcześniejszych przyjęć oznacza wybór art. 18h. Odznaczone: starszy system — 40% za 15 lat, dalszy rok +2,6 pp. Granica ustawowa to 1.01.2013, a nie początek 2012 r. Nie można zastosować starszego systemu do faktycznego pierwszego przyjęcia od 2013 r. bez ustawowego wyjątku.",
    "service_months": "Łączna liczba pełnych miesięcy służby i zaliczonych okresów równorzędnych z zaświadczenia. 25 lat = 300 miesięcy, 15 lat = 180. Nie dodawaj tu cywilnych okresów wpisywanych niżej ani drugi raz nakładających się okresów. W rozdziale 1a urlop wychowawczy najwyżej 36 miesięcy.",
    "qualifying_25_months": "Część łącznej wysługi spełniająca szczególny warunek art. 15aa ust. 3: służba i art. 13 ust. 1 pkt 1, 1d, 2 lub 5–8. Nie wszystkie okresy równorzędne kwalifikują się. Jeśli nie masz takich wyłączeń, wpisz tyle, ile wynosi łączna wysługa. To nie jest dodatkowy staż.",
    "pre_contrib_months": "Pełne miesiące okresów składkowych poprzedzających służbę. Art. 15: pierwsze 36 miesięcy po 2,6 pp/rok, dalsze po 1,3 pp/rok. Art. 15aa: po spełnieniu szczególnego warunku 25 lat po 1,3 pp/rok. Art. 15a i rozdział 1a nie doliczają ich do tej emerytury.",
    "pre_noncontrib_months": "Pełne miesiące okresów nieskładkowych przed służbą, dopuszczone do uwzględnienia po zastosowaniu ograniczeń ustawy FUS. Kalkulator nie ustala sam limitu tych okresów. Przyrost 0,7 pp/rok dotyczy art. 15/15e.",
    "post_contrib_months": "Miesiące po zwolnieniu, które mogą być doliczone na wniosek. Art. 14: emerytura poniżej 75%, wymagany wiek lub inwalidztwo oraz pozostałe warunki. Art. 15aa: szczególne 25 lat i emerytura poniżej 75%. Nie wpisuj przewidywanej dalszej służby — ta należy do łącznej wysługi.",
    "post_conditions": "Zaznacz dopiero po sprawdzeniu warunków doliczenia na wniosek. Dla art. 14 wymagany jest m.in. wiek 55 lat dla mężczyzny / 50 dla kobiety albo inwalidztwo. Art. 15aa ma inne warunki. Sprawdź też termin wniosku i skutki OFE/FUS.",
    "special_case": "Zaznacz, jeżeli historia może podlegać art. 15c w związku ze służbą z art. 13b. Zwykły wzór zostanie zablokowany: konieczna jest analiza dokumentów IPN, wyjątków i właściwych orzeczeń.",
    "fus_service_used": "Chodzi o emeryturę FUS, w której uwzględniono już okresy służby i równorzędne, a nie o każdą emeryturę cywilną. Zaznaczenie blokuje zwykłe wyliczenie z uwagi na art. 12.",
    "exclusion": "Dotyczy ustawowych wyłączeń prawa z art. 10, np. wskazanych prawomocnych skazań. Zaznaczenie blokuje standardowy wzór; wymaga indywidualnego sprawdzenia.",
    "base_mode": "Gotowa podstawa: kwota już ustalona według właściwych przepisów. Składniki uposażenia: ostatnie stanowisko w starszym systemie, poza SM/SC/SCS. 10 kolejnych lat: rozdział 1a i SM/SC/SCS; to średnia wskaźników, nie zwykła średnia pensji.",
    "base": "Miesięczna podstawa wymiaru brutto, nie wysokość emerytury i nie wypłata netto. Powinna zawierać właściwe dodatki, przeliczenie nagrody, wyłączenia i ewentualne waloryzacje między zwolnieniem a ustaleniem prawa. Używana tylko w trybie „gotowa podstawa”.",
    "salary": "Miesięczne należne uposażenie zasadnicze brutto na ostatnim stanowisku. Pole działa tylko w trybie „składniki uposażenia”. Wpisz kwotę należną bez pomniejszeń z tytułów wymienionych w art. 5 ust. 4.",
    "permanent": "Suma miesięcznych stałych dodatków brutto uwzględnianych ustawowo w podstawie, np. za stopień. Nie wpisuj świadczeń wyłączonych, np. teleinformatycznego, ani nagrody rocznej wpisywanej osobno.",
    "annual_award": "Należna nagroda roczna brutto za cały rok, nie jej miesięczna część. Aplikacja podzieli wpisaną kwotę przez 12. Używane wyłącznie w trybie składników ostatniego uposażenia.",
    "longevity": "Miesięczne świadczenie za długoletnią służbę w wysokości należnej przy zwolnieniu. W trybach składników i 10 lat jest doliczane osobno po 32 latach wysługi. W gotowej podstawie musi być już zawarte — program nie doda go drugi raz. Nie myl ze stałym dodatkiem za wysługę.",
    "current_reference": "Urzędowa miesięczna kwota przeciętnego uposażenia właściwa dla Twojej służby na dzień zwolnienia. Program przemnoży ją przez średnią rocznych wskaźników z 10 lat. To nie jest Twoja indywidualna ostatnia pensja.",
    "minimum": "Najniższa emerytura brutto właściwa dla daty ustalenia prawa. 1978,49 zł dotyczy marca 2026–lutego 2027. Wpisanie 0 wyłącza uzupełnienie minimum i zostanie zaznaczone w raporcie. Dla innych dat sprawdź kwotę w ZER MSWiA.",
    "fus_pension": "Miesięczna kwota odrębnej emerytury FUS brutto, używana wyłącznie do reguły uzupełnienia sumy do minimum w systemach, których dotyczy art. 18 ust. 3. Nie zostaje doliczona do wypłaty mundurowej ani symulacji. Jeśli nie dotyczy, wpisz 0.",
    "disability": "Zaznacz przy orzeczonym inwalidztwie pozostającym w związku ze służbą. Daje +15 pp w starszym systemie i limit 80% (81% z Medalem). Nie działa w rozdziale 1a i nie oznacza wyliczania renty inwalidzkiej.",
    "medal": "Zaznacz tylko po przyznaniu Medalu im. podkomisarza Policji Andrzeja Struja. Podwyższenie wynosi 1 pp podstawy; odpowiednio rośnie limit do 76% lub 81%. Dotyczy obu systemów.",
    "pit2": "Zaznacz, jeśli złożyłeś PIT-2 (albo płatnik emerytury i tak uwzględnia kwotę zmniejszającą). Wtedy zaliczka na PIT jest pomniejszona o 300 zł miesięcznie (3600 zł rocznie, czyli kwota wolna 30 000 zł). Bez tego podatek jest wyższy o 300 zł, a różnicę odzyskasz w rozliczeniu rocznym.",
    "work_income": "Miesięczny przychód BRUTTO z działalności objętej ubezpieczeniem społecznym: umowa o pracę, zlecenie albo własna firma (podstawa składek). Umowa o dzieło zwykle się nie wlicza. Wpisz 0, jeśli nie dorabiasz. Rozliczenie następuje po roku, więc liczy się średni przychód.",
    "income_limit_low": "70% przeciętnego miesięcznego wynagrodzenia - do tej kwoty przychodu emerytura nie jest zmniejszana. Zmienia się co kwartał; od 1.09.2026 do 30.11.2026 wynosi 6463,20 zł (M.P. 2026 poz. 839). Od grudnia sprawdź nowy komunikat Prezesa ZUS.",
    "income_limit_high": "130% przeciętnego miesięcznego wynagrodzenia - powyżej tej kwoty emerytura mundurowa jest zmniejszona o 25% (w ZUS byłaby zawieszona). Od 1.09.2026 do 30.11.2026 wynosi 12 003,10 zł (M.P. 2026 poz. 839).",
    "max_reduction": "Najwyższa kwota, o jaką można zmniejszyć emeryturę, gdy przychód mieści się między 70% a 130% (art. 104 ust. 8 pkt 1 ustawy o FUS). Od 1.03.2026 wynosi 989,41 zł (M.P. 2026 poz. 220); waloryzowana co roku w marcu. Dodatkowo zmniejszenie nie przekroczy 25% emerytury.",
    "forecast_years": "Liczba lat kalendarzowych symulacji, od 1 do 60. Pierwszy rok może obejmować tylko część miesięcy. Zmiany roczne z tabeli muszą mieścić się w wybranym horyzoncie.",
    "growth": "Procentowy wzrost przy waloryzacji: wpisz 4 dla mnożnika 1,04, nie 104. To Twoje założenie przyszłej stopy, nie urzędowa prognoza. Waloryzacja od marca nie obniża świadczenia; dozwolone 0–100%.",
    "inflation": "Założona inflacja roczna w procentach. Służy wyłącznie do pokazania realnej siły nabywczej; nie zmienia kwoty wypłaty nominalnej. Dozwolone od -50% do 100%. Przykładowe 2,5% nie jest prognozą urzędową.",
    "year": "Rok kalendarzowy RRRR. Dla podstawy wymagane jest dokładnie 10 kolejnych lat, bez powtórzeń, najpóźniej rok zwolnienia. Dla waloryzacji rok musi należeć do horyzontu symulacji.",
    "pay": "Suma należnych kwot uposażenia brutto za dany rok po korektach wymaganych art. 18f. Nie wpisuj kwoty miesięcznej. Mieszane służby i szczególne wynagrodzenia wymagają wcześniejszego przeliczenia danych.",
    "reference": "Urzędowa roczna kwota przeciętnego uposażenia dla właściwej służby i roku. Musi być większa od zera. Roczna suma Twojego uposażenia zostanie podzielona przez tę kwotę i wyrażona w procentach.",
    "kind": "2%/rok — nurkowie/zwalczanie fizyczne terroryzmu; 1%/rok — m.in. loty, jednostki pływające, skoki, saperzy, wywiad za granicą; 0,5%/rok — warunki szczególne. Strefa wojny daje 0,5 pp za rozpoczęty miesiąc. Wymagane ustawowe normy i potwierdzenie.",
    "start": "Pierwszy zaliczony miesiąc podwyższenia w formacie RRRR-MM (lub MM.RRRR), np. 2010-01. Dla stawek rocznych podaj okres już zaliczony przez jednostkę po spełnieniu norm; dla strefy wojny miesiąc rozpoczęty jest uwzględniany.",
    "end": "Ostatni zaliczony miesiąc podwyższenia w formacie RRRR-MM (lub MM.RRRR), np. 2010-12. Miesiąc końcowy jest wliczany. Okres musi mieścić się między pierwszym właściwym przyjęciem a zwolnieniem.",
    "confirmed": "Zaznaczasz, że sprawdzono nie tylko stanowisko, ale także normy roczne, daty obowiązywania i zaliczenie okresu w dokumentacji jednostki. Kalkulator nie zastępuje zaświadczenia.",
    "unit": "pp podstawy: 2 przy podstawie 10 000 zł daje 200 zł. % emerytury: 2 przy emeryturze 7 000 zł daje 140 zł. zł miesięcznie: bezpośrednia kwota. Każda własna pozycja jest symulacją poza wynikiem ustawowym.",
    "value": "Dodatnia wartość własnego dodatku lub 0. Jej znaczenie zależy od jednostki. Możesz użyć przecinka dziesiętnego. Własny dodatek nie zmienia prawa do świadczenia ani limitu ustawowego.",
    "indexed": "Zaznaczone: początkowa kwota własnego dodatku będzie rosła według zadanej waloryzacji marcowej. Odznaczone: kwota pozostaje stała nominalnie we wszystkich latach.",
    "enabled": "Włącz lub wyłącz pozycję bez jej usuwania. Wyłączony dodatek nie wpływa na wynik ani wykres, ale pozostaje zapisany w profilu.",
}

# Kolumny tabeli symulacji: (nazwa nagłówka, opis pokazywany po najechaniu myszą).
# Te same nazwy trafiają do CSV i raportu. "mies." oznacza miesięczną kwotę z grudnia danego roku.
FORECAST_COLUMNS = (
    ("Rok", "Rok kalendarzowy symulacji. Pierwszy rok bywa niepełny: wypłaty liczone są od następnego pełnego miesiąca po zwolnieniu ze służby."),
    ("Waloryzacja %", "Waloryzacja zastosowana w tym roku od 1 marca (Twoje założenie z zakładki Symulacja albo wyjątek dla tego roku). 0 oznacza, że w tym roku emerytura nie była waloryzowana, np. gdy prawo do niej ustalono po 1 marca."),
    ("Wariant (mies.)", "Miesięczna emerytura brutto w grudniu tego roku RAZEM z własnymi dodatkami z zakładki „Dodatki”. Bez dodatków jest równa kolumnie „Ustawa (mies.)”."),
    ("Ustawa (mies.)", "Miesięczna emerytura brutto w grudniu tego roku wyliczona wyłącznie z reguł ustawy, bez własnych dodatków."),
    ("Wartość realna", "Kwota z kolumny „Wariant (mies.)” przeliczona na ceny z początku pierwszego roku symulacji, przy założonej inflacji. Pokazuje, ile za tę emeryturę kupisz w dzisiejszych pieniądzach. Gdy inflacja przewyższa waloryzację, wartość realna maleje."),
    ("Netto (mies.)", "Miesięczna emerytura z grudnia po odjęciu składki zdrowotnej 9% i zaliczki na PIT (bez dorabiania). To kwota „na rękę” z kolumny „Wariant (mies.)”."),
    ("Wypłacone w roku", "Suma brutto faktycznie wypłacona w tym roku kalendarzowym: tylko miesiące, w których emerytura jest wypłacana, styczeń i luty przed waloryzacją, marzec–grudzień po niej."),
    ("Wypłacone razem", "Suma kolumny „Wypłacone w roku” od początku symulacji do końca tego roku (brutto, w cenach z danego okresu, bez przeliczania na wartość realną)."),
)

# Tabela „Jak zmienia się emerytura w zależności od przychodu” (zakładka Netto i dorabianie).
EARNINGS_COLUMNS = (
    ("Przychód z pracy", "Miesięczny przychód brutto z pracy w cywilnej firmie. Wiersze to: próg 70%, środek strefy zmniejszeń, próg 130% oraz kwota tuż powyżej tego progu."),
    ("Zmniejszenie", "O ile miesięcznie spadnie emerytura brutto przy takim przychodzie."),
    ("Emerytura brutto", "Emerytura brutto po zmniejszeniu."),
    ("Emerytura netto", "Emerytura po zmniejszeniu, po odjęciu składki zdrowotnej 9% i zaliczki na PIT."),
)

# Wykres: których linii dotyczą pola wyboru - patrz CHART_SERIES w gui.py.
