# Weryfikacja EMKA 0.1.1

Ten dokument opisuje, co i jak sprawdzono, a czego nie. Nie jest opinią prawną ani potwierdzeniem zgodności z przepisami.

## Kto sprawdzał

Autor. Nie robił tego prawnik ani specjalista od emerytur mundurowych, a wyników nie porównano z oficjalnym wyliczeniem organu emerytalnego. Przepisy sprawdzono 29.10.2026, testy i przegląd bezpieczeństwa wykonano 31.10.2026.

## Co porównano z przepisami

Wzory i progi w `emka/engine.py` porównano z tekstem jednolitym ustawy z 18.02.1994 (Dz.U. 2026 poz. 505, tekst ujednolicony z 10.07.2026, pobrany z ELI). Rozbieżności nie znaleziono w tych miejscach:

- progi stażu: 15 lat w starszym systemie i 25 lat w rozdziale 1a (art. 12 ust. 1, art. 18b ust. 1), bez wymogu wieku,
- przyrosty: 40% + 2,6 pp za rok (art. 15 ust. 1), 60% + 3 pp (art. 18e), okresy składkowe i nieskładkowe przed służbą,
- podwyższenia 2/1/0,5 pp za rok, strefa wojny za rozpoczęty miesiąc, Medal +1 pp, inwalidztwo +15 pp (art. 15 ust. 2–5),
- art. 15a, 15aa i 15ab: zakresy dat oraz 1,3 pp przy 25 latach służby,
- doliczanie okresów po zwolnieniu (art. 14 i art. 15aa ust. 4–7): 1,3 pp za rok, emerytura poniżej 75%,
- zbieg podwyższeń za ten sam okres (art. 17),
- limity 75/80/76/81% oraz najniższa emerytura z uzupełnieniem sumy z FUS (art. 18, 18g),
- wybór rozdziału 1a (art. 18h),
- podstawa wymiaru: ostatnie uposażenie albo 10 lat, zaokrąglenie rocznych wskaźników do 0,01%, świadczenie za długoletnią służbę po 32 latach (art. 5, art. 18f ust. 3),
- waloryzacja tylko dla praw ustalonych przed 1 marca (art. 6 pkt 1 lit. a),
- organ emerytalny (art. 32).

Opis w `emka/PRZEPISY.md` (artykuły, progi, stawki i normy roczne z § 2–5 rozporządzenia, np. 40 godzin lotów, 12 dni pracy sapera) porównano 31.10.2026 z tekstem ustawy (Dz.U. 2026 poz. 505) i rozporządzenia (Dz.U. 2020 poz. 1611) z ELI. Poprawiono wtedy opis norm dla jednostek pływających, art. 40c i art. 6.

Dorabianie sprawdzono z art. 41 ustawy mundurowej i art. 104 ustawy o FUS (Dz.U. 2025 poz. 1749): zmniejszenie nie przekracza 25% emerytury, powyżej 130% emerytura maleje o 25% i nie jest zawieszana, a przy emeryturze co najmniej 75% podstawy (bez +15 pp) nie ma zmniejszeń. Kwoty pochodzą z komunikatów: progi od 1.09.2026 z M.P. 2026 poz. 839, a maksymalne zmniejszenie 989,41 zł z M.P. 2026 poz. 220. Najniższą emeryturę 1978,49 zł i wskaźnik waloryzacji 105,3% potwierdza komunikat Prezesa ZUS z 17.02.2026.

## Czego nie sprawdzono w tekście urzędowym

- **PIT i składka zdrowotna.** Stawki na 2026 r. (12% i 32%, próg 120 000 zł, 3600 zł, składka 9%) pochodzą z opracowań, a nie z Dz.U. Kontrola: najniższa emerytura 1978,49 zł daje 1800,43 zł netto, zgodnie z danymi prasowymi o emeryturze minimalnej.
- **Nowelizacja Dz.U. 2025 poz. 1820.** Jej opis (dodatkowe okresy równorzędne SC i SCS, zmiana art. 15aa) pochodzi z wcześniejszej analizy. Normy roczne podwyższeń program i tak nie stosuje: okresy wpisuje użytkownik po potwierdzeniu w jednostce.
- **Waloryzacja.** Zasad z art. 88 i następnych ustawy o FUS (coroczna waloryzacja od 1 marca) nie porównywano z tekstem urzędowym. Art. 6 ustawy mundurowej sprawdzono.
- **Wiek a dorabianie.** Nie ma źródła urzędowego, które wprost potwierdzałoby, że ustawa mundurowa nie wyłącza zmniejszeń po osiągnięciu wieku emerytalnego. Wniosek wynika tylko z braku takiego przepisu w art. 41 i w art. 104 ust. 1–8 ustawy o FUS. Warto go potwierdzić w ZER MSWiA.

## Testy

Zestaw ma 127 testów. Lokalnie uruchomiono go na macOS z Pythonem 3.11.4 i Tk 8.6. Bez sesji graficznej 21 testów okien jest pomijanych, a pozostałe 106 przechodzi.

Testy obejmują:

- granice dat (1/2.01.1999, 2012/2013), progi 15 i 25 lat, pełne miesiące, okresy cywilne,
- art. 15aa i 18h, limity, Medal, inwalidztwo, zbieg podwyższeń, metodę 10 lat, minimum i FUS,
- netto, dorabianie, waloryzację, inflację, formaty dat,
- zapis i odczyt profili, eksport CSV i raportu, zachowanie przy spreparowanych plikach,
- brak modułów sieciowych w kodzie, narzędzia wydania i zasady w plikach workflow (zagrożenia opisuje [STRIDE.md](STRIDE.md)).

Wyników nie porównywano z żadnym oficjalnym wyliczeniem. Nie oceniano też wyglądu okna na zrzutach ekranu.

Workflow `tests` na GitHubie uruchamia testy na Linuksie (Python 3.10, 3.12, 3.13), Windows i macOS. Ostatni przebieg zakończył się powodzeniem.

## Pliki wykonywalne

Pliki powstają w PyInstallerze 6 i każdy przechodzi `--self-test` po zbudowaniu. Wydanie 0.1.1 zbudowano na GitHubie dla Windows, macOS (arm64) i Linuksa (x86_64). Windows i Linuksa nie testowano ręcznie na komputerze z pulpitem. Workflow w Gitei nie był jeszcze sprawdzany.

Cały zestaw z oknami uruchomisz tak:

```sh
EMKA_GUI_TEST=1 python3 -m unittest discover -s tests -v
```
