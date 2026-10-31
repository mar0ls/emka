# Weryfikacja EMKA 0.1.1

Przepisy sprawdzono 29.10.2026. Testy i przegląd bezpieczeństwa wykonano 31.10.2026.

## Zgodność z ustawą

Reguły sprawdzono z tekstem jednolitym ustawy z 18.02.1994 (Dz.U. 2026 poz. 505, tekst ujednolicony z 10.07.2026), pobranym z ELI i porównanym artykuł po artykule z kodem:

| Przepis | Co sprawdzono | Wynik |
|---|---|---|
| art. 12 ust. 1, art. 18b ust. 1 | progi 15 lat (starszy system) i 25 lat (rozdział 1a); brak wymogu wieku (art. 18d uchylony) | zgodne |
| art. 15 ust. 1 | 40% + 2,6 pp za rok; składkowe przed służbą 2,6 pp (max 3 lata) i 1,3 pp; nieskładkowe 0,7 pp | zgodne |
| art. 15 ust. 2–5 | podwyższenia 2/1/0,5 pp za rok, 0,5 pp za rozpoczęty miesiąc strefy wojny, Medal +1 pp, inwalidztwo +15 pp, pełne miesiące | zgodne |
| art. 15a, 15aa, 15ab | zakres dat (od 2.01.1999; 2.01.1999–30.09.2003), 1,3 pp przy 25 latach służby i okresów z art. 13 ust. 1 pkt 1, 1d, 2, 5–8, doliczanie po zwolnieniu przy emeryturze <75% | zgodne |
| art. 14 ust. 1–4 | doliczanie po zwolnieniu: 1,3 pp za rok, emerytura <75%, wiek 55/50 lat albo inwalidztwo | zgodne |
| art. 17 | zbieg podwyższeń za ten sam okres: tylko jedno (nie dotyczy +15 pp) | zgodne |
| art. 18, 18g | limity 75/80/76/81%; minimum i uzupełnienie sumy z FUS tylko dla art. 15a/15d i rozdziału 1a | zgodne |
| art. 18e, 18h | 60% + 3 pp; strefa wojny; Medal; wybór rozdziału 1a dla przyjętych przed 2013 | zgodne |
| art. 5 ust. 1, 1a, 1c, 3, 4; art. 18f ust. 3 | podstawa: ostatnie uposażenie albo 10 lat (SM, SC, SCS i rozdział 1a); zaokrąglenie rocznych wskaźników do 0,01%; świadczenie za długoletnią służbę po 32 latach | zgodne |
| art. 6 pkt 1 lit. a | waloryzacja obejmuje świadczenia z prawem ustalonym przed 1 marca | zgodne |
| art. 32 | organ emerytalny (MSWiA, wojskowy dla SKW/SWW, MS dla SW) | zgodne |

Dorabianie i netto:

| Przepis / źródło | Co sprawdzono | Wynik |
|---|---|---|
| art. 41 ust. 1, 3, 4 ustawy | zmniejszenie max 25%, powyżej 130% zmniejszenie o 25% (bez zawieszenia), wyłączenie przy emeryturze ≥75% podstawy bez +15 pp | zgodne |
| art. 104 ust. 1–8, 10 ustawy o FUS (Dz.U. 2025 poz. 1749) | definicja przychodu, strefa 70–130%, kwota maksymalna | zgodne |
| M.P. 2026 poz. 839 | progi od 1.09.2026: 6463,20 zł i 12 003,10 zł | zgodne |
| M.P. 2026 poz. 220 | maksymalne zmniejszenie emerytury 989,41 zł | zgodne |
| PIT 2026 (12%/32%, 120 000 zł, 3600 zł), składka zdrowotna 9% | tylko opracowania, nie Dz.U.; kontrola: 1978,49 zł → 1800,43 zł netto zgodnie z danymi prasowymi o emeryturze minimalnej | wiarygodne, niezweryfikowane w Dz.U. |

Nie ma źródła urzędowego, które wprost potwierdzałoby, że ustawa mundurowa nie wyłącza zmniejszeń po osiągnięciu wieku emerytalnego. Taki wniosek wynika tylko z braku takiego przepisu w art. 41 oraz w art. 104 ust. 1–8 ustawy o FUS. Warto go potwierdzić w ZER MSWiA.

Kwoty urzędowe: najniższa emerytura 1978,49 zł i wskaźnik waloryzacji 105,3% od 1.03.2026 potwierdzone komunikatem Prezesa ZUS z 17.02.2026.

Nie sprawdzono w tekście urzędowym (te elementy pochodzą z wcześniejszej analizy): szczegółowych norm rocznych z rozporządzenia RM (Dz.U. 2020 poz. 1611), art. 88–89 ustawy o FUS (zasady waloryzacji i zaokrągleń) oraz nowelizacji Dz.U. 2025 poz. 1820. Okresy z podwyższeniami użytkownik wpisuje sam, po potwierdzeniu w jednostce.

We wzorach i progach błędu nie znaleziono. Przed wydaniem poprawiono natomiast:

- Wysługa była sprawdzana tylko z dokładnością do miesiąca kalendarzowego. Przy przyjęciu np. 15.01.2001 i zwolnieniu 31.10.2026 program dopuszczał 310 miesięcy, a pełnych jest 309. Zawyżenie wysługi zawyżało emeryturę o 2,6/12 pp podstawy za każdy miesiąc. Teraz sprawdzane są dokładne daty.
- Pole „świadczenie za długoletnią służbę” blokowało obliczenia w trybie „gotowa podstawa”, choć w tym trybie nie jest używane.
- Komunikaty błędów pokazywały nazwy techniczne pól (np. `service_months`) zamiast etykiet z formularza.
- Kolumna „Styczeń brutto” w CSV w rzeczywistości oznacza kwotę przed marcową waloryzacją (w pierwszym roku wypłat styczeń może nie być wypłacany). Zmieniono nazwę na „Przed marcową waloryzacją brutto”.
- `calculate()` zmieniał przekazany profil (zamieniał pola tekstowe na liczby).

## Testy

- Wszystkie 127 testów przechodzi. W tym 21 testów okien, które wymagają sesji graficznej: uruchomiono je na macOS z Pythonem 3.11.4 i Tk 8.6. Bez sesji graficznej te 21 jest pomijanych, a pozostałe 106 przechodzi.
- Test różnicowy starego i nowego silnika na 20 000 losowych profili dał takie same wyniki liczbowe wszędzie tam, gdzie oba silniki liczą. Różnią się tylko komunikaty błędów oraz 18 przypadków, w których nowa, dokładniejsza kontrola dat odrzuca zawyżoną wysługę.
- Testy obejmują granice dat 1/2.01.1999 i 2012/2013, fakultatywne art. 15aa i 18h, progi 15 i 25 lat, pełne miesiące, okresy cywilne, limity, Medal, inwalidztwo, zbieg podwyższeń, metodę 10 lat, minimum i FUS, własne dodatki, marcową waloryzację, inflację, roczne wskaźniki, formaty dat, profile JSON i eksporty.
- Osobne testy sprawdzają zachowanie przy spreparowanych plikach, brak modułów sieciowych w kodzie, narzędzia wydania i zasady w plikach workflow. Zagrożenia opisuje [STRIDE.md](STRIDE.md).
- Nie wykonano wizualnej oceny okna (zrzutów ekranu). Testy jednostkowe uruchomiono lokalnie tylko na macOS. Workflow `tests` (Linux z Pythonem 3.10, 3.12 i 3.13, Windows, macOS) jest przygotowany, ale nie był jeszcze uruchomiony.

Pliki wykonywalne (PyInstaller 6, `make`): macOS arm64 zbudowany i sprawdzony przez `--self-test`. Linux x86_64 i aarch64 zbudowane w Dockerze (Debian bookworm) i sprawdzone pod xvfb. Windows: workflow `build` uruchomiony ręcznie na GitHubie zbudował plik i przeszedł `--self-test`. Nie testowano go ręcznie na komputerze z pulpitem. Skrypty wydania (`tools/release.py`, `tools/gitea_release.py`) są przetestowane na atrapie serwera, ale publikacja wydania z tagu (zadanie `release` na GitHubie) i workflow w Gitei nie były jeszcze uruchomione.

Pełny zestaw w sesji graficznej:

```sh
EMKA_GUI_TEST=1 python3 -m unittest discover -s tests -v
```
