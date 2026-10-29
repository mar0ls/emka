@echo off
cd /d "%~dp0"
py -3 -m emka
if errorlevel 1 (
  echo Wymagany Python 3.10 lub nowszy z Tcl/Tk. Sprawdz: py -3 -m tkinter
  pause
)
