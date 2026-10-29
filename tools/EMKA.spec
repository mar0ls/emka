# -*- mode: python ; coding: utf-8 -*-
# Definicja budowania dla PyInstallera: jeden plik dla Windows i Linuksa, pakiet .app dla macOS.
# Uruchamiaj przez `make` (patrz Makefile), nie bezpośrednio.
import re
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
ASSETS = ROOT / "emka" / "assets"
VERSION = re.search(r'__version__ = "(.+?)"', (ROOT / "emka" / "__init__.py").read_text(encoding="utf-8")).group(1)

analysis = Analysis(
    [str(ROOT / "tools" / "pyinstaller_entry.py")],
    pathex=[str(ROOT)],
    # Pliki czytane w czasie działania (zakładka „Przepisy” i ikona okna).
    datas=[(str(ROOT / "emka" / "PRZEPISY.md"), "emka"), (str(ASSETS / "icon.png"), "emka/assets")],
    excludes=["unittest", "pydoc", "doctest"],
)
pyz = PYZ(analysis.pure)

if sys.platform == "darwin":
    exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name="EMKA", console=False)
    collected = COLLECT(exe, analysis.binaries, analysis.datas, name="EMKA")
    app = BUNDLE(
        collected, name="EMKA.app", icon=str(ASSETS / "EMKA.icns"), bundle_identifier="pl.emka.app",
        info_plist={"CFBundleShortVersionString": VERSION, "NSHighResolutionCapable": True},
    )
else:
    exe = EXE(
        pyz, analysis.scripts, analysis.binaries, analysis.datas, [], name="EMKA", console=False,
        icon=str(ASSETS / "icon.ico") if sys.platform == "win32" else None,
    )
