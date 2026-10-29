#!/bin/sh
# Wypisuje ścieżkę pierwszego Pythona 3.10+ z biblioteką Tk. Niczego nie instaluje ani nie pobiera.
# Używają go run.sh i Makefile. Kod wyjścia 1 = nie znaleziono.
cd "$(dirname "$0")/.."

for candidate in "${EMKA_PYTHON:-}" ".venv/bin/python" python3 python3.13 python3.12 python3.11 python3.10 \
    "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"; do
  [ -n "$candidate" ] || continue
  command -v "$candidate" >/dev/null 2>&1 || continue
  if "$candidate" -c 'import sys; assert sys.version_info >= (3, 10); import tkinter' >/dev/null 2>&1; then
    command -v "$candidate"
    exit 0
  fi
done
exit 1
