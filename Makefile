# EMKA - budowanie samodzielnego programu (PyInstaller).
#
#   make mac | win | linux | all      (make bez argumentów pokazuje pomoc)
#
# PyInstaller nie buduje krzyżowo: plik dla danego systemu trzeba zbudować na tym systemie.
# Wyjątek: Linuksa da się zbudować na innym systemie w kontenerze Docker.
# Windows i macOS najłatwiej zbudować w CI - patrz .github/workflows/build.yml.

VERSION := $(shell sed -n 's/^__version__ = "\(.*\)"/\1/p' emka/__init__.py)
ARCH := $(shell uname -m 2>/dev/null)

# Obraz i platforma używane do budowy Linuksa poza Linuksem.
# Na Macu z Apple Silicon domyślnie powstanie wersja arm64; dla x86_64: make linux DOCKER_PLATFORM=linux/amd64
DOCKER_IMAGE ?= python:3.12-bookworm
DOCKER_PLATFORM ?=

ifeq ($(OS),Windows_NT)
HOST := win
PYTHON ?= python
else
PYTHON ?= $(shell tools/find_python.sh 2>/dev/null)
ifeq ($(shell uname -s),Darwin)
HOST := mac
else
HOST := linux
endif
endif

.DEFAULT_GOAL := help
.PHONY: help all mac win linux test check-python clean distclean

help:
	@echo "EMKA $(VERSION) - budowanie programu wykonywalnego"
	@echo ""
	@echo "  make mac      aplikacja macOS (EMKA.app + zip)        - tylko na macOS"
	@echo "  make win      EMKA-$(VERSION)-windows.exe             - tylko na Windows"
	@echo "  make linux    EMKA-$(VERSION)-linux-<arch>            - na Linuksie albo przez Docker"
	@echo "  make all      wszystko, co da się zbudować na tym komputerze (reszta: komunikat)"
	@echo "  make test     testy jednostkowe"
	@echo "  make clean    usuwa build/ i dist/;  make distclean usuwa też .build-venv/"
	@echo ""
	@echo "Ten komputer: $(HOST).  Python: $(if $(PYTHON),$(PYTHON),NIE ZNALEZIONO - ustaw PYTHON=/sciezka/do/python3)"

check-python:
	@test -n "$(PYTHON)" || { echo "Nie znaleziono Pythona 3.10+ z Tk. Wskaż go: make $(HOST) PYTHON=/sciezka/do/python3"; exit 1; }

test: check-python
	@test -n "$(PYTHON)" || { echo "Nie znaleziono Pythona. Ustaw PYTHON=..."; exit 1; }
	$(PYTHON) -m unittest discover -s tests

ifeq ($(HOST),mac)
mac: check-python
	$(PYTHON) tools/build.py
else
mac:
	@echo "make mac: aplikację macOS można zbudować tylko na macOS (ten komputer: $(HOST))."
	@echo "Użyj CI: .github/workflows/build.yml (runner macos)."
	@exit 1
endif

ifeq ($(HOST),win)
win: check-python
	$(PYTHON) tools/build.py
else
win:
	@echo "make win: plik .exe można zbudować tylko na Windows (ten komputer: $(HOST))."
	@echo "Użyj CI: .github/workflows/build.yml (runner windows) albo uruchom 'make win' na Windows."
	@exit 1
endif

ifeq ($(HOST),linux)
linux: check-python
	$(PYTHON) tools/build.py
else
linux:
	@command -v docker >/dev/null 2>&1 || { echo "make linux: na systemie $(HOST) potrzebny jest Docker (albo zbuduj na Linuksie)."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "make linux: Docker jest zainstalowany, ale nie działa. Uruchom Docker Desktop."; exit 1; }
	docker run --rm $(if $(DOCKER_PLATFORM),--platform $(DOCKER_PLATFORM)) --user "$$(id -u):$$(id -g)" -e HOME=/tmp \
		-v "$(CURDIR)":/src -w /src $(DOCKER_IMAGE) \
		sh -c "python -m pip install --quiet --user pyinstaller && python tools/build.py --current-python --skip-self-test --workpath /tmp/build"
	@echo "Self-test w kontenerze z wirtualnym ekranem (xvfb)..."
	docker run --rm $(if $(DOCKER_PLATFORM),--platform $(DOCKER_PLATFORM)) -v "$(CURDIR)/dist":/dist $(DOCKER_IMAGE) \
		sh -c 'apt-get update -qq >/dev/null && apt-get install -y -qq xvfb >/dev/null 2>&1 && xvfb-run -a "$$(ls -t /dist/EMKA-*-linux-* | head -1)" --self-test'
endif

# Buduje to, co da się na tym komputerze: system własny, Linuksa przez Docker (jeśli działa); resztę pomija z wyjaśnieniem.
all:
	@$(MAKE) --no-print-directory $(HOST)
	@for target in mac linux win; do \
		if [ "$$target" = "$(HOST)" ]; then continue; fi; \
		if [ "$$target" = linux ] && command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
			$(MAKE) --no-print-directory linux || exit 1; \
		else \
			echo "POMINIĘTO $$target: nie da się go zbudować na systemie $(HOST) (użyj CI - .github/workflows/build.yml)."; \
		fi; \
	done
	@echo ""; echo "Gotowe pliki w dist/:"; ls -1 dist | grep -v '^EMKA$$'

clean:
	rm -rf build dist

distclean: clean
	rm -rf .build-venv
