#!/bin/sh
# Nadaje gotowym plikom w dist/ docelowe nazwy z wersją i architekturą.  Użycie: package.sh mac|linux|win
set -eu
cd "$(dirname "$0")/.."
version=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' emka/__init__.py)
arch=$(uname -m)

case "$1" in
  mac)
    rm -rf dist/EMKA  # katalog pośredni; gotowy jest dist/EMKA.app
    zip="dist/EMKA-$version-macos-$arch.zip"
    rm -f "$zip"
    ditto -c -k --keepParent dist/EMKA.app "$zip"
    echo "Gotowe: dist/EMKA.app oraz $zip" ;;
  linux)
    mv -f dist/EMKA "dist/EMKA-$version-linux-$arch"
    echo "Gotowe: dist/EMKA-$version-linux-$arch" ;;
  win)
    mv -f dist/EMKA.exe "dist/EMKA-$version-windows.exe"
    echo "Gotowe: dist/EMKA-$version-windows.exe" ;;
  *) echo "Nieznany system: $1" >&2; exit 2 ;;
esac
