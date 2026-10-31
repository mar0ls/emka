"""Buduje samodzielny program EMKA dla systemu, na którym jest uruchomiony (PyInstaller).

Użycie:  python tools/build.py [--current-python] [--skip-self-test] [--workpath KATALOG]

Działa tak samo na Windows, macOS i Linuksie i nie wymaga `make` ani powłoki sh - dlatego używa go też CI.
Domyślnie tworzy środowisko `.build-venv` z PyInstallerem (potrzebny internet przy pierwszym uruchomieniu).
`--current-python` pomija środowisko i używa bieżącego Pythona, który ma już PyInstallera (np. w kontenerze).
Python musi mieć Tk (`python -m tkinter`).
"""
import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def host_target():
    return {"darwin": "mac", "win32": "win"}.get(sys.platform, "linux")


def read_version():
    text = (ROOT / "emka" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'^__version__ = "(.+?)"', text, re.MULTILINE).group(1)


def run(command):
    print("+", " ".join(str(part) for part in command), flush=True)
    subprocess.run([str(part) for part in command], cwd=ROOT, check=True)


def venv_python():
    folder = "Scripts" if sys.platform == "win32" else "bin"
    return ROOT / ".build-venv" / folder / ("python.exe" if sys.platform == "win32" else "python")


def ensure_venv():
    """Środowisko z PyInstallerem; tworzone raz."""
    python = venv_python()
    if not python.exists():
        venv.create(ROOT / ".build-venv", with_pip=True)
        run([python, "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
        run([python, "-m", "pip", "install", "--quiet", "-r", ROOT / "tools" / "requirements-build.txt"])
    return python


def package(target, version):
    """Nadaje wynikowym plikom docelowe nazwy z wersją i architekturą. Zwraca ścieżkę do pliku do sprawdzenia."""
    arch = platform.machine().lower()
    if target == "mac":
        shutil.rmtree(DIST / "EMKA", ignore_errors=True)  # katalog pośredni; gotowy jest EMKA.app
        archive = DIST / f"EMKA-{version}-macos-{arch}.zip"
        archive.unlink(missing_ok=True)
        run(["ditto", "-c", "-k", "--keepParent", DIST / "EMKA.app", archive])  # zachowuje dowiązania w .app
        print(f"Gotowe: {DIST / 'EMKA.app'} oraz {archive}")
        return DIST / "EMKA.app" / "Contents" / "MacOS" / "EMKA"
    if target == "win":
        final = DIST / f"EMKA-{version}-windows.exe"
        final.unlink(missing_ok=True)
        (DIST / "EMKA.exe").rename(final)
    else:
        final = DIST / f"EMKA-{version}-linux-{arch}"
        final.unlink(missing_ok=True)
        (DIST / "EMKA").rename(final)
    print(f"Gotowe: {final}")
    return final


def self_test(executable, target):
    """Uruchamia gotowy program z `--self-test`; bez wyświetlacza (Linux) pomija z komunikatem."""
    if target == "linux" and not os.environ.get("DISPLAY"):
        print("Pominięto self-test: brak wyświetlacza (DISPLAY). Uruchom przez xvfb-run.")
        return
    run([executable, "--self-test"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--current-python", action="store_true", help="użyj bieżącego Pythona z PyInstallerem")
    parser.add_argument("--skip-self-test", action="store_true")
    parser.add_argument("--workpath", default="build")
    args = parser.parse_args()

    target, version = host_target(), read_version()
    python = Path(sys.executable) if args.current_python else ensure_venv()
    print(f"EMKA {version}: budowanie dla systemu '{target}' ({platform.machine()})")
    run([python, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", "dist",
         "--workpath", args.workpath, "tools/EMKA.spec"])
    executable = package(target, version)
    if not args.skip_self_test:
        self_test(executable, target)


if __name__ == "__main__":
    main()
