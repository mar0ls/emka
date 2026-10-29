"""Punkt wejścia dla PyInstallera (nie uruchamia się przez `python -m`).

`--self-test` buduje okno bez wyświetlania go, liczy przykładowy profil i kończy z kodem 0 albo 1.
Sprawdza więc, że w gotowym pliku są Tk, dane (PRZEPISY.md) i ikona. Używa tego `make`.
"""
import sys


def self_test():
    from emka.gui import App

    app = App()
    app.withdraw()
    ok = app.result is not None and hasattr(app, "icon") and app.amount.cget("text") != "—"
    app.destroy()
    print("EMKA self-test:", "OK" if ok else "BŁĄD")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    from emka.gui import main

    main()
