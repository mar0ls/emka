"""Pomocnik wydań, używany przez CI i ręcznie.

    python tools/release.py check-tag v0.1.0    # tag musi odpowiadać wersji z kodu i mieć wpis w CHANGELOG.md
    python tools/release.py notes [0.1.0]       # wypisuje opis wydania z CHANGELOG.md
    python tools/release.py checksums KATALOG   # zapisuje KATALOG/SHA256SUMS dla plików w katalogu

Tylko biblioteka standardowa, działa tak samo na Windows, macOS i Linuksie.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$")


def read_version():
    text = (ROOT / "emka" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'^__version__ = "(.+?)"', text, re.MULTILINE).group(1)


def changelog_section(version, text=None):
    """Treść wpisu `## [wersja] - data` z CHANGELOG.md albo None, gdy wpisu nie ma."""
    if text is None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    start = re.search(rf"^## \[{re.escape(version)}\].*$", text, re.MULTILINE)
    if not start:
        return None
    following = re.search(r"^## \[", text[start.end():], re.MULTILINE)
    end = start.end() + following.start() if following else len(text)
    return text[start.end():end].strip()


def check_tag(tag):
    """Zwraca listę problemów; pusta lista = tag można wydać."""
    version = read_version()
    problems = []
    if not VERSION_PATTERN.match(version):
        problems.append(f"Wersja „{version}” w emka/__init__.py nie ma postaci X.Y.Z.")
    if tag != f"v{version}":
        problems.append(f"Tag „{tag}” nie zgadza się z wersją w kodzie (oczekiwano v{version}).")
    if not changelog_section(version):
        problems.append(f"CHANGELOG.md nie ma wpisu „## [{version}]” albo jest pusty.")
    return problems


def write_checksums(folder):
    """Zapisuje SHA256SUMS w formacie zrozumiałym dla `sha256sum -c` i `shasum -a 256 -c`."""
    folder = Path(folder)
    lines = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS":
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (folder / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def main(argv):
    command = argv[1] if len(argv) > 1 else ""
    if command == "check-tag" and len(argv) == 3:
        problems = check_tag(argv[2])
        for problem in problems:
            print("BŁĄD:", problem, file=sys.stderr)
        return 1 if problems else 0
    if command == "notes" and len(argv) in (2, 3):
        notes = changelog_section(argv[2] if len(argv) == 3 else read_version())
        if not notes:
            print("BŁĄD: brak wpisu w CHANGELOG.md", file=sys.stderr)
            return 1
        print(notes)
        return 0
    if command == "checksums" and len(argv) == 3:
        print("\n".join(write_checksums(argv[2])))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
