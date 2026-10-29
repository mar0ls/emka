#!/bin/bash
set -eu
cd "$(dirname "$0")"

# Pierwszy dostępny Python z Tk (szczegóły w tools/find_python.sh).
if emka_python="$(tools/find_python.sh)"; then
  exec "$emka_python" -m emka
fi
echo "Nie znaleziono Pythona 3.10+ z biblioteką Tk."
echo "Zainstaluj Pythona z obsługą Tcl/Tk lub wskaż go przez EMKA_PYTHON."
echo "Sprawdzenie instalacji: python3 -m tkinter"
exit 1
