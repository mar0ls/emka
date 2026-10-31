# Składniki zewnętrzne

Kod EMKA jest na licencji MIT (plik `LICENSE`) i używa wyłącznie biblioteki standardowej Pythona.
Samodzielne pliki wykonywalne (`EMKA-*.exe`, `EMKA.app`, `EMKA-*-linux-*`) powstają w PyInstallerze
i zawierają dodatkowo cudze składniki:

| Składnik | Do czego | Licencja |
|---|---|---|
| Python (interpreter i biblioteka standardowa) | uruchamia program | PSF License, https://docs.python.org/3/license.html |
| Tcl/Tk | okna programu | licencja w stylu BSD, https://www.tcl-lang.org/software/tcltk/license.html |
| PyInstaller (tylko program ładujący w pliku wynikowym) | uruchamia spakowany program | GPL 2 z wyjątkiem dla programów spakowanych, https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt |

Pliki te nie są modyfikowane. Pełne teksty licencji znajdziesz pod podanymi adresami oraz w instalacji
Pythona (plik `LICENSE.txt`). Ikona programu jest autorska i objęta tą samą licencją MIT co kod.
