"""Okienkowy interfejs (Tk/ttk). Wszystkie dane zostają na komputerze użytkownika."""
import copy
import re
import textwrap
import tkinter as tk
import webbrowser
from dataclasses import fields
from decimal import Decimal
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from . import __version__
from .engine import (AnnualPay, BONUS_RATES, Bonus, Extra, FIELD_LABELS, MONTH_FIELDS, Profile,
                     RULE_DATE, SERVICES, calculate, earnings_effect, earnings_table, forecast,
                     full_months_between, integer, net_pension, number, parse_date, parse_month,
                     service_rules)
from .helptext import EARNINGS_COLUMNS, FORECAST_COLUMNS, HELP
from .storage import export_csv, load_profile, report, save_profile

# Kolory i czcionka całego programu.
BG, INK, MUTED, ACCENT, LINE = "#f3f6fa", "#15253d", "#586b81", "#176bce", "#dce4ee"
INFO_BG, INFO_FG = "#edf5ff", "#245887"
ERROR_FG = "#b42318"
FONT = "Helvetica"
GOOD_FG = "#24856b"
ICON_PATH = Path(__file__).with_name("assets") / "icon.png"

# Linie na wykresie: (pole w ForecastRow, indeks kolumny w FORECAST_COLUMNS, kolor, czy zaznaczona domyślnie).
CHART_SERIES = (
    ("december", 2, ACCENT, True),
    ("legal_december", 3, GOOD_FG, True),
    ("real_december", 4, "#ce7b24", True),
    ("net_december", 5, "#7b4fc9", False),
)
LAW_URL = "https://eli.gov.pl/eli/DU/2026/505/ogl/pol"
TEXT_WIDTH = 650  # szerokość (px) zawijanych opisów na stronach formularza


def format_pln(amount):
    """1234.5 -> '1 234,50 zł'"""
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",") + " zł"


class Popup:
    """Okienko z opisem (chmurka). Zarządza oknem; podklasy decydują, kiedy i gdzie je pokazać."""

    DELAY_MS = 450

    def __init__(self, widget):
        self.widget = widget
        self.timer = None
        self.window = None

    def schedule_at(self, text, x, y_below, y_above):
        """Pokaże chmurkę po krótkim opóźnieniu, żeby nie migała przy szybkim ruchu myszy."""
        self.hide()
        self.timer = self.widget.after(self.DELAY_MS, lambda: self.show_at(text, x, y_below, y_above))

    def show_at(self, text, x, y_below, y_above):
        """Chmurka w poziomie `x`: pod `y_below`, a gdy się nie mieści - nad `y_above`. Zawsze w obrębie ekranu."""
        self.hide()
        if not self.widget.winfo_exists():
            return
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.attributes("-topmost", True)
        tk.Label(self.window, text=text, justify="left", wraplength=370, bg="#fffbe8", fg=INK,
                 relief="solid", borderwidth=1, padx=14, pady=12, font=(FONT, 12)).pack()
        self.window.update_idletasks()

        screen_w, screen_h = self.widget.winfo_screenwidth(), self.widget.winfo_screenheight()
        x = min(x, screen_w - self.window.winfo_reqwidth() - 12)
        y = y_below
        if y + self.window.winfo_reqheight() > screen_h - 12:
            y = max(12, y_above - self.window.winfo_reqheight() - 7)
        self.window.geometry(f"+{max(0, x)}+{max(0, y)}")

    def hide(self, event=None):
        if self.timer:
            self.widget.after_cancel(self.timer)
            self.timer = None
        if self.window:
            self.window.destroy()
            self.window = None


class Tooltip(Popup):
    """Pomoc przy polu: po najechaniu myszą (z lekkim opóźnieniem) albo po F1."""

    def __init__(self, widget, text):
        super().__init__(widget)
        self.text = text
        widget.bind("<Enter>", self.on_enter, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")
        widget.bind("<FocusOut>", self.hide, add="+")
        widget.bind("<F1>", self.show, add="+")
        widget.bind("<Destroy>", self.hide, add="+")

    def position(self):
        """Domyślnie chmurka pojawia się pod polem."""
        return (self.widget.winfo_rootx() + 12, self.widget.winfo_rooty() + self.widget.winfo_height() + 7,
                self.widget.winfo_rooty())

    def on_enter(self, event=None):
        self.schedule_at(self.text, *self.position())

    def show(self, event=None):
        self.show_at(self.text, *self.position())


class HeadingTooltip(Popup):
    """Chmurki z opisem kolumn tabeli. Nagłówki Treeview nie są osobnymi widgetami, więc śledzimy ruch myszy."""

    def __init__(self, tree, texts):
        super().__init__(tree)
        self.texts = texts  # opisy w kolejności kolumn
        self.column = None  # kolumna, nad którą jest teraz mysz
        tree.bind("<Motion>", self.on_motion, add="+")
        tree.bind("<Leave>", self.on_leave, add="+")
        tree.bind("<ButtonPress>", self.on_leave, add="+")
        tree.bind("<Destroy>", self.hide, add="+")

    def column_text(self, column_id):
        """Opis kolumny o identyfikatorze Treeview: '#1', '#2'... (puste, gdy brak)."""
        match = re.fullmatch(r"#(\d+)", column_id or "")
        index = int(match.group(1)) - 1 if match else -1
        return self.texts[index] if 0 <= index < len(self.texts) else ""

    def on_motion(self, event):
        in_heading = self.widget.identify_region(event.x, event.y) == "heading"
        column = self.widget.identify_column(event.x) if in_heading else None
        if column == self.column:
            return  # nadal ta sama kolumna - nie ruszamy chmurki
        self.column = column
        self.hide()
        text = self.column_text(column)
        if text:
            self.schedule_at(text, event.x_root + 12, event.y_root + 22, event.y_root - 15)

    def on_leave(self, event=None):
        self.column = None
        self.hide()


class ScrollFrame(ttk.Frame):
    """Strona z pionowym paskiem przewijania; zawartość dodajemy do `.body`."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas, padding=22, style="White.TFrame")
        self.window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Obszar przewijania dopasowuje się do zawartości, a zawartość do szerokości okna.
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window, width=e.width))

    def scroll(self, event):
        """Obsługa kółka myszy: Windows/macOS (<MouseWheel>) oraz Linux (przyciski 4 i 5)."""
        if event.num == 4:
            lines = -1
        elif event.num == 5:
            lines = 1
        elif abs(event.delta) >= 120:  # Windows podaje wielokrotności 120
            lines = -int(event.delta / 120)
        else:  # macOS podaje małe liczby
            lines = -int(event.delta)
        self.canvas.yview_scroll(lines, "units")


class Editor(tk.Toplevel):
    """Małe okno do dodania lub edycji jednej pozycji tabeli.

    `specs` to lista (klucz, etykieta, opcje), gdzie opcje to:
    krotka wartości (lista wyboru), `bool` (pole wyboru) albo `None` (zwykłe pole tekstowe).
    `on_accept` dostaje słownik wartości; może zgłosić ValueError - wtedy pokazujemy błąd w oknie.
    """

    def __init__(self, parent, title, specs, initial, on_accept):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        self.configure(bg="white")
        self.on_accept = on_accept
        self.variables = {}

        body = ttk.Frame(self, padding=22, style="White.TFrame")
        body.pack(fill="both", expand=True)
        first_input = None
        for key, label, options in specs:
            if options is bool:
                variable = tk.BooleanVar(value=initial.get(key, False))
                widget = ttk.Checkbutton(body, text=label, variable=variable)
                widget.pack(anchor="w", pady=9)
            else:
                ttk.Label(body, text=label).pack(anchor="w", pady=(8, 3))
                variable = tk.StringVar(value=str(initial.get(key, "")))
                if options:
                    widget = ttk.Combobox(body, textvariable=variable, values=options, state="readonly", width=52)
                else:
                    widget = ttk.Entry(body, textvariable=variable, width=55)
                widget.pack(fill="x")
                first_input = first_input or widget
            self.variables[key] = variable
            Tooltip(widget, HELP.get(key, "Nazwa własnej pozycji, widoczna w zestawieniu i raporcie."))

        self.error = ttk.Label(body, text="", foreground=ERROR_FG, wraplength=450)
        self.error.pack(fill="x", pady=8)
        ttk.Button(body, text="Zapisz pozycję", command=self.accept, style="Accent.TButton").pack(side="right", pady=8)
        ttk.Button(body, text="Anuluj", command=self.destroy).pack(side="left", pady=8)

        self.bind("<Return>", lambda e: self.accept())
        self.bind("<Escape>", lambda e: self.destroy())
        if first_input is not None:
            first_input.focus_set()
        self.grab_set()

    def accept(self):
        values = {key: variable.get() for key, variable in self.variables.items()}
        try:
            self.on_accept(values)
        except (ValueError, TypeError) as exc:
            self.error.configure(text=str(exc))
            return
        self.destroy()


INLINE_MARKDOWN = re.compile(r"(\*\*.+?\*\*|\[[^\]]+\]\(https?://[^)\s]+\))")
LINK_MARKDOWN = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def show_markdown(widget, markdown):
    """Wstawia do pola Text prosty Markdown: nagłówki, pogrubienia, linki, listy i tabele.

    Dzięki temu zakładka „Przepisy” nie pokazuje surowych znaczników (`**`, `##`, `[tekst](adres)`).
    """
    widget.tag_configure("h1", font=(FONT, 18, "bold"), spacing1=4, spacing3=8)
    widget.tag_configure("h2", font=(FONT, 14, "bold"), foreground=ACCENT, spacing1=16, spacing3=4)
    widget.tag_configure("bold", font=(FONT, 12, "bold"))
    widget.tag_configure("link", foreground=ACCENT, underline=True)
    widget.tag_configure("row", lmargin1=12, lmargin2=12, spacing1=3, background="#f5f8fc")

    def insert_inline(text, *tags):
        for part in INLINE_MARKDOWN.split(text):
            if not part:
                continue
            link = LINK_MARKDOWN.fullmatch(part)
            if part.startswith("**") and part.endswith("**"):
                widget.insert("end", part[2:-2], tags + ("bold",))
            elif link:
                label, url = link.groups()
                tag = f"link-{widget.index('end')}"
                widget.insert("end", label, tags + ("link", tag))
                widget.tag_bind(tag, "<Button-1>", lambda e, target=url: webbrowser.open(target))
                widget.tag_bind(tag, "<Enter>", lambda e: widget.configure(cursor="hand2"))
                widget.tag_bind(tag, "<Leave>", lambda e: widget.configure(cursor=""))
            else:
                widget.insert("end", part, tags)

    table_header_next = True
    for line in markdown.splitlines():
        if not line.startswith("|"):
            table_header_next = True
        if line.startswith("# "):
            insert_inline(line[2:], "h1")
        elif line.startswith("## "):
            insert_inline(line[3:], "h2")
        elif line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if all(set(cell) <= set("-:") for cell in cells):  # linia |---|---|
                continue
            for i, cell in enumerate(cells):
                if i:
                    widget.insert("end", "   │   ", "row")
                insert_inline(cell, "row", *(("bold",) if table_header_next else ()))
            table_header_next = False
        elif line.startswith("- "):
            widget.insert("end", "•  ")
            insert_inline(line[2:])
        else:
            insert_inline(line)
        widget.insert("end", "\n")


# Walidacja pozycji z tabel - zgłasza ValueError z czytelnym komunikatem.
def _check_annual_pay(data):
    data["year"] = integer(data["year"], "Rok", 1900, 2200)
    number(data["pay"], "Roczne uposażenie")
    number(data["reference"], "Roczne przeciętne uposażenie", Decimal("0.01"))


def _check_extra(data):
    number(data["value"], "Wartość")


def _check_bonus(data):
    if parse_month(data["start"]) > parse_month(data["end"]):
        raise ValueError("Początek okresu musi być przed końcem.")


RECORD_CHECKS = {AnnualPay: _check_annual_pay, Extra: _check_extra, Bonus: _check_bonus}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"EMKA {__version__} · Emerytura funkcjonariusza")
        # Okno dopasowane do mniejszych ekranów (np. laptop 1280 px).
        self.geometry(f"{min(1380, self.winfo_screenwidth() - 60)}x{min(920, self.winfo_screenheight() - 100)}")
        self.minsize(1100, 680)
        self.configure(bg=BG)
        self.set_icon()

        self.profile = Profile()
        self.result = None  # ostatni policzony wynik; None = dane zmienione od ostatniego liczenia
        self.rows = []  # wiersze symulacji dla ostatniego wyniku
        self.snapshots = []  # zapamiętane scenariusze do porównania
        self.loading = True  # podczas wczytywania nie reagujemy na zmiany pól
        self.vars = {}

        self.setup_style()
        self.build_header()
        self.build_toolbar()
        main = ttk.Frame(self, padding=(20, 0, 20, 12))
        main.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(side="left", fill="both", expand=True, padx=(0, 16))
        self.build_result_panel(main)
        self.status = tk.StringVar(value=f"Reguły sprawdzone: {RULE_DATE} · Dane przykładowe — zastąp swoimi.")
        tk.Label(self, textvariable=self.status, bg=BG, fg=MUTED, anchor="w", padx=22, pady=7,
                 font=(FONT, 10)).pack(fill="x")

        self.create_variables()
        for build_page in (self.build_data, self.build_basis, self.build_bonus, self.build_extras,
                           self.build_net, self.build_forecast, self.build_comparison, self.build_law):
            build_page()

        # Powiązania między polami (dopiero po zbudowaniu formularza).
        self.vars["first_entry"].trace_add("write", self.sync_system_from_date)
        self.vars["regime"].trace_add("write", self.sync_regime)
        self.vars["new_system"].trace_add("write", self.sync_group)
        self.loading = False
        self.refresh_rule_context()

        self.bind("<Command-s>", lambda e: self.save())
        self.bind("<Control-s>", lambda e: self.save())
        self.bind("<F5>", lambda e: self.calculate_show())
        self.bind_all("<MouseWheel>", self.on_mousewheel)
        self.bind_all("<Button-4>", self.on_mousewheel)
        self.bind_all("<Button-5>", self.on_mousewheel)
        self.calculate_show()

    # ---------------------------------------------------------------- układ okna

    def set_icon(self):
        """Ikona okna i (na macOS/Linuksie) ikona w docku. Brak pliku nie może blokować programu."""
        try:
            self.icon = tk.PhotoImage(file=str(ICON_PATH))  # trzeba trzymać referencję
            self.iconphoto(True, self.icon)
        except tk.TclError:
            pass

    def setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=(FONT, 12), foreground=INK)
        style.configure("TFrame", background=BG)
        style.configure("White.TFrame", background="white")
        style.configure("TLabel", background="white", padding=(0, 2))
        style.configure("Hint.TLabel", foreground=MUTED, background="white", font=(FONT, 11))
        style.configure("Heading.TLabel", font=(FONT, 18, "bold"), background="white")
        style.configure("TButton", padding=(12, 9), borderwidth=0)
        style.configure("Accent.TButton", background=ACCENT, foreground="white")
        style.map("Accent.TButton", background=[("active", "#1055a7")])
        style.configure("TEntry", padding=7)
        style.configure("TCombobox", padding=6)
        style.configure("TCheckbutton", background="white", padding=(0, 5))
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(8, 12), background="#e8eef5")
        style.map("TNotebook.Tab", background=[("selected", "white")], foreground=[("selected", ACCENT)])
        style.configure("Treeview", rowheight=30, background="white", fieldbackground="white", borderwidth=0)
        style.configure("Treeview.Heading", background="#e8eef5", padding=8, font=(FONT, 11, "bold"))

    def build_header(self):
        header = tk.Frame(self, bg=INK, padx=26, pady=18)
        header.pack(fill="x")
        tk.Label(header, text="EMKA", fg="white", bg=INK, font=(FONT, 27, "bold")).pack(side="left")
        tk.Label(header, text="  /  Emerytura funkcjonariusza", fg="#b9cbe2", bg=INK,
                 font=(FONT, 15)).pack(side="left")
        tk.Label(header, text="LOKALNIE  ·  BRUTTO", fg="#93c8ff", bg=INK,
                 font=(FONT, 10, "bold")).pack(side="right")

    def build_toolbar(self):
        toolbar = ttk.Frame(self, padding=(20, 12))
        toolbar.pack(fill="x")
        buttons = (("Otwórz profil", self.open_profile), ("Zapisz profil", self.save),
                   ("Eksport CSV", self.csv), ("Raport", self.export_report))
        for title, command in buttons:
            ttk.Button(toolbar, text=title, command=command).pack(side="left", padx=(0, 7))
        ttk.Button(toolbar, text="Oblicz emeryturę  →", command=self.calculate_show,
                   style="Accent.TButton").pack(side="right")

    def build_result_panel(self, parent):
        """Prawy panel z wynikiem - widoczny na każdej zakładce."""
        side = ttk.Frame(parent, style="White.TFrame", width=330, padding=20)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        ttk.Label(side, text="TWÓJ WYNIK", style="Hint.TLabel").pack(anchor="w")
        self.amount = ttk.Label(side, text="—", font=(FONT, 29, "bold"), foreground=ACCENT)
        self.amount.pack(anchor="w", pady=(10, 0))
        ttk.Label(side, text="miesięcznie brutto · reguły ustawy", style="Hint.TLabel").pack(anchor="w")
        self.net_label = ttk.Label(side, text="", font=(FONT, 14, "bold"), foreground=GOOD_FG)
        self.net_label.pack(anchor="w", pady=(10, 0))
        self.system_label = ttk.Label(side, text="", wraplength=285)
        self.system_label.pack(anchor="w", pady=(18, 8))
        self.scenario_label = ttk.Label(side, text="", wraplength=285, font=(FONT, 13, "bold"))
        self.scenario_label.pack(anchor="w", pady=6)
        self.work_label = ttk.Label(side, text="", wraplength=285, foreground=ERROR_FG)
        self.work_label.pack(anchor="w")
        self.result_text = ScrolledText(side, width=30, height=18, wrap="word", font=(FONT, 11), bg="white",
                                        fg=INK, relief="flat", borderwidth=0, highlightthickness=0,
                                        state="disabled")
        self.result_text.pack(fill="both", expand=True, pady=10)
        ttk.Button(side, text="Dodaj wynik do porównania", command=self.add_snapshot).pack(fill="x", pady=(10, 0))

    def create_variables(self):
        """Dla każdego pola profilu tworzy zmienną Tk, która jest źródłem prawdy dla formularza.

        Listy (podwyższenia, dodatki, lata) i wyjątki roczne trzymamy bezpośrednio w `self.profile`.
        """
        for f in fields(Profile):
            default = getattr(self.profile, f.name)
            if f.name == "new_system":
                variable = tk.BooleanVar(value=False)  # w profilu może być None, w oknie zawsze tak/nie
            elif isinstance(default, bool):
                variable = tk.BooleanVar(value=default)
            elif isinstance(default, (str, int)):
                variable = tk.StringVar(value=str(default))
            else:
                continue
            variable.trace_add("write", self.changed)
            self.vars[f.name] = variable

    def on_mousewheel(self, event):
        """Przewija aktualną stronę, chyba że kursor jest nad polem, które przewija się samo."""
        if isinstance(event.widget, (tk.Text, ttk.Treeview)):
            return
        try:
            if event.widget.winfo_toplevel() is not self:  # np. okno edycji pozycji
                return
        except AttributeError:
            return
        selected_tab = self.notebook.select()
        if selected_tab:
            self.nametowidget(selected_tab).scroll(event)

    # ---------------------------------------------------------- pomocnicy formularza

    def page(self, title):
        page = ScrollFrame(self.notebook)
        self.notebook.add(page, text=title)
        return page.body

    def heading(self, frame, title, hint=""):
        ttk.Label(frame, text=title, style="Heading.TLabel").pack(anchor="w", pady=(4, 8))
        if hint:
            ttk.Label(frame, text=hint, style="Hint.TLabel", wraplength=TEXT_WIDTH,
                      justify="left").pack(fill="x", pady=(0, 16))

    def field(self, frame, key, title, choices=None, hint=""):
        """Wiersz formularza: etykieta, pole (lub lista wyboru) i ikonka ⓘ z pomocą."""
        row = ttk.Frame(frame, style="White.TFrame")
        row.pack(fill="x", pady=6)
        label = ttk.Label(row, text=title, wraplength=300)
        label.pack(side="left", anchor="w", padx=(0, 10))
        if choices:
            widget = ttk.Combobox(row, textvariable=self.vars[key], values=choices, state="readonly", width=24)
        else:
            widget = ttk.Entry(row, textvariable=self.vars[key], width=26)
        widget.pack(side="right")
        help_icon = ttk.Label(row, text="ⓘ", foreground=ACCENT, cursor="question_arrow")
        help_icon.pack(side="right", padx=8)

        help_text = HELP.get(key, hint or title)
        tips = {target: Tooltip(target, help_text) for target in (label, widget, help_icon)}
        # Ikonkę można też kliknąć (przydatne na ekranach dotykowych).
        help_icon.bind("<ButtonRelease-1>", tips[help_icon].show)

        if hint:
            ttk.Label(frame, text=hint, style="Hint.TLabel", wraplength=TEXT_WIDTH).pack(anchor="w", pady=(0, 6))
        return widget

    def check(self, frame, key, text):
        widget = ttk.Checkbutton(frame, text=textwrap.fill(text, 82), variable=self.vars[key])
        widget.pack(anchor="w", pady=3)
        Tooltip(widget, HELP.get(key, text))

    def divider(self, frame):
        ttk.Separator(frame).pack(fill="x", pady=18)

    def table(self, parent, columns, add, edit, delete):
        """Tabela z przyciskami „Dodaj” i „Usuń” oraz edycją po dwukliku."""
        wrap = ttk.Frame(parent, style="White.TFrame")
        wrap.pack(fill="x", pady=10)
        tree = ttk.Treeview(wrap, columns=columns, show="headings", height=6, selectmode="browse")
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=max(80, 610 // len(columns)), minwidth=65, stretch=True)
        tree.pack(fill="x")
        controls = ttk.Frame(wrap, style="White.TFrame")
        controls.pack(fill="x", pady=(8, 0))
        ttk.Button(controls, text="+ Dodaj", command=add).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Usuń zaznaczoną", command=delete).pack(side="left")
        ttk.Label(controls, text="Dwuklik: edycja", style="Hint.TLabel").pack(side="right")
        tree.bind("<Double-1>", lambda e: edit())
        return tree

    # ------------------------------------------------------------------- zakładki

    def build_data(self):
        f = self.page("1  Dane")
        self.heading(f, "Twoja służba",
                     "Wpisz pełne miesiące wysługi z dokumentacji. Daty określają system, a suma miesięcy "
                     "uwzględnia przerwy i potwierdzone okresy równorzędne.")
        ttk.Label(f, text="Najedź na pole lub ⓘ, aby zobaczyć podpowiedź. W aktywnym polu możesz też nacisnąć F1. "
                          "Daty wpisuj jako RRRR-MM-DD albo DD.MM.RRRR.",
                  style="Hint.TLabel", wraplength=TEXT_WIDTH).pack(anchor="w", pady=(0, 10))
        self.field(f, "name", "Nazwa profilu")
        self.field(f, "service", "Służba", SERVICES)
        self.field(f, "first_entry", "Pierwsze właściwe przyjęcie",
                   hint="Uwzględnij wcześniejszą służbę i wyjątki art. 18a ust. 2; nie wpisuj daty ostatniego powrotu do służby.")
        self.field(f, "release", "Zwolnienie / planowane odejście")
        self.field(f, "right_date", "Data ustalenia prawa do świadczenia",
                   hint="Wpływa na pierwszą waloryzację. Dla planu wpisz zakładaną datę; aplikacja nie wyznacza terminu decyzji.")
        self.check(f, "new_system",
                   "Nowy system: przyjęcie od 1.01.2013 — 25 lat / 60% (dla wcześniejszych przyjęć: wybór art. 18h)")
        self.group_context = ttk.Label(f, text="", style="Hint.TLabel", wraplength=TEXT_WIDTH)
        self.group_context.pack(fill="x", pady=(0, 8))
        self.field(f, "regime", "Sposób ustalenia emerytury", ("auto", "15aa", "18h"),
                   "auto: system wg daty; 15aa: wybór dla przyjętych 2.01.1999–30.09.2003; 18h: wybór rozdziału 1a.")
        self.rule_context = ttk.Label(f, text="", wraplength=TEXT_WIDTH, justify="left", foreground=INFO_FG,
                                      background=INFO_BG, padding=14)
        self.rule_context.pack(fill="x", pady=(8, 14))
        self.field(f, "service_months", "Łączna wysługa służby — miesiące",
                   hint="Bez okresów cywilnych wpisywanych poniżej. W rozdziale 1a urlop wychowawczy uwzględnij maksymalnie do 36 miesięcy.")
        self.months_hint = ttk.Label(f, text="", style="Hint.TLabel", wraplength=TEXT_WIDTH)
        self.months_hint.pack(anchor="w", pady=(0, 6))
        self.field(f, "qualifying_25_months", "W tym miesiące do warunku art. 15aa",
                   hint="Tylko art. 13 ust. 1 pkt 1, 1d, 2 lub 5–8. Wartość nie może przekraczać łącznej wysługi.")

        self.divider(f)
        self.heading(f, "Okresy cywilne",
                     "Kalkulator doliczy je wyłącznie w systemie, który na to pozwala. "
                     "Okresy nieskładkowe podaj już po ograniczeniach wynikających z ustawy FUS.")
        self.field(f, "pre_contrib_months", "Składkowe przed służbą — miesiące")
        self.field(f, "pre_noncontrib_months", "Nieskładkowe przed służbą — miesiące")
        self.field(f, "post_contrib_months", "Do doliczenia po służbie — miesiące")
        self.check(f, "post_conditions",
                   "Potwierdzam warunki doliczenia po służbie: wniosek, a dla art. 14 również wymagany wiek lub inwalidztwo")

        self.divider(f)
        self.heading(f, "Przypadki wymagające odrębnej analizy",
                     "Zaznaczenie blokuje zwykłe wyliczenie — tych przypadków nie da się sprowadzić do standardowego wzoru.")
        self.check(f, "special_case", "Może mieć zastosowanie art. 15c / historia służby z art. 13b")
        self.check(f, "fus_service_used", "Służba została już uwzględniona w emeryturze FUS (art. 12)")
        self.check(f, "exclusion", "Występuje wyłączenie prawa określone w art. 10")

    def build_basis(self):
        f = self.page("2  Podstawa")
        self.heading(f, "Podstawa wymiaru",
                     "Kwoty należne brutto. Wyłącz świadczenie teleinformatyczne; uwzględnij przepisy dotyczące "
                     "nieobecności. Gotowa podstawa ma już zawierać wszystkie właściwe składniki i przeliczenia.")
        self.field(f, "base_mode", "Sposób obliczenia", ("gotowa podstawa", "składniki uposażenia", "10 kolejnych lat"))
        self.field(f, "base", "Gotowa podstawa — zł")

        self.divider(f)
        self.heading(f, "Ostatnie uposażenie",
                     "Dla starszego systemu poza SM/SC/SCS. Pola poniżej są używane tylko w trybie „składniki uposażenia”.")
        self.field(f, "salary", "Uposażenie zasadnicze — zł/mies.")
        self.field(f, "permanent", "Stałe dodatki — zł/mies.")
        self.field(f, "annual_award", "Należna nagroda roczna — zł/rok")
        self.field(f, "longevity", "Świadczenie za długoletnią służbę — zł",
                   hint="W trybie składników i 10 lat doliczane osobno dopiero po 32 latach wysługi. "
                        "Gotowa podstawa już zawiera ten składnik — nie jest dodawany ponownie.")

        self.divider(f)
        self.heading(f, "10 kolejnych lat — art. 18f",
                     "Dla rozdziału 1a oraz SM/SC/SCS. Wprowadź sumy roczne i odpowiadające im urzędowe roczne "
                     "przeciętne uposażenia. Każdy stosunek zaokrąglamy do 0,01%, następnie liczymy średnią wskaźników.")
        self.field(f, "current_reference", "Przeciętne uposażenie na dzień zwolnienia")
        self.pay_tree = self.table(
            f, ("Rok", "Roczne należne uposażenie", "Roczne przeciętne uposażenie"),
            add=self.edit_pay, edit=lambda: self.edit_pay(True),
            delete=lambda: self.delete_record("annual_pay", self.pay_tree))

        self.divider(f)
        self.heading(f, "Minimum i FUS",
                     "Kwota FUS służy do sprawdzenia uzupełnienia do minimum. Nie jest doliczana do wypłaty mundurowej.")
        self.field(f, "minimum", "Najniższa emerytura — zł (0 = wyłącz)",
                   hint="1978,49 zł: marzec 2026–luty 2027. Dla innych dat ustaw właściwą wartość.")
        self.field(f, "fus_pension", "Odrębna emerytura FUS — zł/mies.")

    def build_bonus(self):
        f = self.page("3  Podwyższenia")
        self.heading(f, "Podwyższenia z ustawy",
                     "Nie są przyznawane za samą przynależność do służby. Wpisz okresy z zaświadczenia po sprawdzeniu "
                     "norm rocznych, właściwych przepisów i dat. Nakładające się miesiące zostaną rozliczone według "
                     "najwyższego podwyższenia.")
        self.check(f, "disability", "+15 pp: orzeczone inwalidztwo pozostające w związku ze służbą (starszy system)")
        self.check(f, "medal", "+1 pp: przyznany Medal im. podkomisarza Policji Andrzeja Struja")

        self.divider(f)
        self.heading(f, "Okresy szczególnej służby",
                     "Roczne: 2% / 1% / 0,5%. Strefa wojny: 0,5 pp za rozpoczęty miesiąc. Podaj początek i koniec "
                     "w formacie RRRR-MM (lub MM.RRRR), włącznie. W rozdziale 1a dostępna jest wyłącznie strefa wojny.")
        self.bonus_tree = self.table(
            f, ("Nazwa", "Rodzaj", "Od", "Do", "Potwierdzone"),
            add=self.edit_bonus, edit=lambda: self.edit_bonus(True),
            delete=lambda: self.delete_record("bonuses", self.bonus_tree))
        ttk.Label(f, text="Szczegółowe warunki: loty ≥40 h/rok; saperzy ≥12 dni; PSP — odpowiednie działania ≥30 dni; "
                          "pozostałe normy i wyjątki opisano w zakładce Przepisy. Potwierdzenie dotyczy zaliczenia "
                          "okresu, nie wyłącznie obecności na stanowisku.",
                  style="Hint.TLabel", wraplength=TEXT_WIDTH).pack(anchor="w", pady=10)

    def build_extras(self):
        f = self.page("4  Dodatki")
        self.heading(f, "Twój wariant symulacyjny",
                     "Dodaj dowolną liczbę fakultatywnych pozycji: punkty procentowe podstawy, procent emerytury albo "
                     "stałą kwotę. Wynik z reguł ustawy pozostaje osobną wartością; własne pozycje nie stanowią "
                     "uprawnienia do świadczenia.")
        self.extra_tree = self.table(
            f, ("Nazwa", "Jednostka", "Wartość", "Waloryzacja", "Aktywny"),
            add=self.edit_extra, edit=lambda: self.edit_extra(True),
            delete=lambda: self.delete_record("extras", self.extra_tree))
        self.divider(f)
        ttk.Label(f, text="Przykład: 2 pp przy podstawie 10 000 zł = 200 zł. Dodatek 2% emerytury 7 000 zł = 140 zł. "
                          "Procenty liczone są od wyniku początkowego; później kwota podlega wybranej waloryzacji. "
                          "Pozycje bez waloryzacji pozostają stałe nominalnie.",
                  wraplength=TEXT_WIDTH, style="Hint.TLabel").pack(anchor="w")

    def build_net(self):
        f = self.page("5  Netto i dorabianie")
        self.heading(f, "Emerytura na rękę",
                     "Od emerytury brutto potrącana jest składka zdrowotna 9% i zaliczka na podatek: 12% "
                     "(32% od nadwyżki ponad 120 000 zł rocznie), pomniejszona o kwotę wolną.")
        self.check(f, "pit2", "Rozliczam emeryturę z kwotą zmniejszającą podatek (PIT-2, 300 zł miesięcznie)")
        self.net_summary = ttk.Label(f, text="", wraplength=TEXT_WIDTH, justify="left", foreground=INFO_FG,
                                     background=INFO_BG, padding=14)
        self.net_summary.pack(fill="x", pady=(10, 4))

        self.divider(f)
        self.heading(f, "Dorabianie w cywilnej firmie",
                     "Jeśli pracujesz na umowie o pracę, zleceniu lub prowadzisz firmę, emerytura mundurowa "
                     "może być zmniejszona. Do 70% przeciętnego wynagrodzenia nic nie tracisz; między 70% a 130% "
                     "emerytura maleje o kwotę przekroczenia (nie więcej niż kwota maksymalna i 25% emerytury); "
                     "powyżej 130% — o 25%. Nie dotyczy to emerytury równej 75% podstawy.")
        self.field(f, "work_income", "Miesięczny przychód brutto z pracy — zł")
        self.field(f, "income_limit_low", "Próg 70% wynagrodzenia — zł")
        self.field(f, "income_limit_high", "Próg 130% wynagrodzenia — zł")
        self.field(f, "max_reduction", "Maks. zmniejszenie (70–130%) — zł",
                   hint="Progi obowiązują od 1.09.2026 do 30.11.2026 i zmieniają się co kwartał (komunikat Prezesa ZUS).")
        self.earn_summary = ttk.Label(f, text="", wraplength=TEXT_WIDTH, justify="left", foreground=INFO_FG,
                                      background=INFO_BG, padding=14)
        self.earn_summary.pack(fill="x", pady=(10, 14))

        ttk.Label(f, text="Jak zmienia się emerytura w zależności od przychodu", style="Heading.TLabel",
                  font=(FONT, 14, "bold")).pack(anchor="w", pady=(4, 6))
        columns = [name for name, _ in EARNINGS_COLUMNS]
        self.earn_tree = ttk.Treeview(f, columns=columns, show="headings", height=4)
        for column in columns:
            self.earn_tree.heading(column, text=column)
            self.earn_tree.column(column, width=150, minwidth=90, anchor="e", stretch=True)
        self.earn_tree.pack(fill="x")
        self.earn_help = HeadingTooltip(self.earn_tree, [text for _, text in EARNINGS_COLUMNS])

    def build_forecast(self):
        f = self.page("6  Symulacja")
        self.heading(f, "Jak może rosnąć emerytura",
                     "Wzrost 4 oznacza waloryzację ×1,04. Obliczenia od 1 marca uwzględniają datę ustalenia prawa. "
                     "Roczne wypłaty obejmują tylko pełne miesiące od zakończenia służby. Wartość realna jest "
                     "w cenach początku pierwszego roku symulacji.")
        self.field(f, "forecast_years", "Horyzont — liczba lat (1–60)")
        self.field(f, "growth", "Domyślny wzrost roczny — %")
        self.field(f, "inflation", "Domyślna inflacja roczna — %")
        self.override_tree = self.table(
            f, ("Rok", "Waloryzacja %", "Inflacja %"),
            add=self.edit_override, edit=lambda: self.edit_override(True), delete=self.delete_override)

        # Wybór linii na wykresie; kolorowa kreska działa jak legenda, opis pojawia się po najechaniu myszą.
        options = ttk.Frame(f, style="White.TFrame")
        options.pack(fill="x", pady=(18, 0))
        ttk.Label(options, text="Na wykresie:", style="Hint.TLabel").pack(side="left", padx=(0, 10))
        self.chart_vars = {}
        for attribute, index, color, default in CHART_SERIES:
            name, description = FORECAST_COLUMNS[index]
            variable = tk.BooleanVar(value=default)
            variable.trace_add("write", lambda *args: self.draw_chart())
            tk.Label(options, text="━━", fg=color, bg="white", font=(FONT, 12, "bold")).pack(side="left")
            box = ttk.Checkbutton(options, text=name, variable=variable)
            box.pack(side="left", padx=(2, 14))
            Tooltip(box, description)
            self.chart_vars[attribute] = variable

        self.chart = tk.Canvas(f, height=250, bg="#f5f8fc", highlightthickness=0)
        self.chart.pack(fill="x", pady=(6, 15))
        self.chart.bind("<Configure>", lambda e: self.draw_chart())

        columns = [name for name, _ in FORECAST_COLUMNS]
        wrap = ttk.Frame(f, style="White.TFrame")
        wrap.pack(fill="x", pady=12)
        self.forecast_tree = ttk.Treeview(wrap, columns=columns, show="headings", height=12)
        for column in columns:
            self.forecast_tree.heading(column, text=column)
            self.forecast_tree.column(column, width=150, minwidth=95, anchor="e", stretch=False)
        self.forecast_tree.column(columns[0], width=70)
        self.forecast_tree.column(columns[1], width=120)
        self.forecast_help = HeadingTooltip(self.forecast_tree, [text for _, text in FORECAST_COLUMNS])
        scrollbar = ttk.Scrollbar(wrap, orient="horizontal", command=self.forecast_tree.xview)
        self.forecast_tree.configure(xscrollcommand=scrollbar.set)
        self.forecast_tree.pack(fill="x")
        scrollbar.pack(fill="x")

    def build_comparison(self):
        f = self.page("Porównanie")
        self.heading(f, "Porównaj swoje scenariusze",
                     "Dodaj bieżący wynik przyciskiem po prawej, zmień dane i dodaj kolejny. Wiersze są niezależnymi "
                     "kopiami konfiguracji w tej sesji. Dwuklik przywraca konfigurację wybranego wariantu. "
                     "Zapisz profile JSON, aby zachować je na później.")
        self.compare_tree = self.table(
            f, ("Profil", "Służba", "System", "Ustawa brutto", "Wariant brutto", "Ostatni rok"),
            add=self.add_snapshot, edit=self.restore_snapshot, delete=self.delete_snapshot)
        self.compare_rules = ttk.Label(
            f, text="Wybierz scenariusz, aby zobaczyć przepisy jego służby i systemu.", wraplength=TEXT_WIDTH,
            justify="left", background=INFO_BG, foreground=INFO_FG, padding=14)
        self.compare_rules.pack(fill="x", pady=15)
        self.compare_tree.bind("<<TreeviewSelect>>", self.show_snapshot_rules)

    def build_law(self):
        f = self.page("Przepisy")
        self.heading(f, "Reguły i źródła",
                     "Przegląd źródeł: 29.10.2026. W przyszłości konieczna ponowna weryfikacja zmian. Dokument opisuje "
                     "warunki wejściowe, algorytm i przypadki, które wymagają indywidualnej analizy.")
        ttk.Button(f, text="Otwórz urzędowy tekst ustawy ↗",
                   command=lambda: webbrowser.open(LAW_URL)).pack(anchor="w", pady=(0, 12))
        self.law_text = ScrolledText(f, wrap="word", width=75, height=36, bg="white", fg=INK, font=(FONT, 12),
                                     relief="flat", borderwidth=0, highlightthickness=0, padx=8, pady=8)
        self.law_text.pack(fill="both", expand=True)
        show_markdown(self.law_text, Path(__file__).with_name("PRZEPISY.md").read_text(encoding="utf-8"))
        self.law_text.configure(state="disabled")

    # ------------------------------------------------- edycja tabel (okna „Dodaj”)

    def selected(self, tree):
        """Indeks zaznaczonego wiersza albo None."""
        selection = tree.selection()
        return int(selection[0]) if selection else None

    def edit_record(self, attribute, tree, record_class, specs, defaults, edit):
        """Dodaje nową pozycję do listy w profilu albo edytuje zaznaczoną."""
        index = self.selected(tree) if edit else None
        if edit and index is None:
            return  # nic nie zaznaczono
        initial = vars(getattr(self.profile, attribute)[index]).copy() if edit else defaults

        def accept(data):
            check = RECORD_CHECKS.get(record_class)
            if check:
                check(data)
            if "name" in data and not data["name"].strip():
                raise ValueError("Podaj nazwę pozycji.")
            items = getattr(self.profile, attribute)
            if index is None:
                items.append(record_class(**data))
            else:
                items[index] = record_class(**data)
            self.refresh_tables()
            self.changed()

        Editor(self, "Edytuj pozycję" if edit else "Dodaj pozycję", specs, initial, accept)

    def edit_pay(self, edit=False):
        specs = [("year", "Rok kalendarzowy", None),
                 ("pay", "Należne uposażenie — suma roczna", None),
                 ("reference", "Przeciętne uposażenie — kwota roczna", None)]
        defaults = vars(AnnualPay(year=2016 + len(self.profile.annual_pay)))
        self.edit_record("annual_pay", self.pay_tree, AnnualPay, specs, defaults, edit)

    def edit_bonus(self, edit=False):
        specs = [("name", "Tytuł podwyższenia / dokument", None),
                 ("kind", "Stawka", tuple(BONUS_RATES)),
                 ("start", "Od — RRRR-MM (włącznie)", None),
                 ("end", "Do — RRRR-MM (włącznie)", None),
                 ("confirmed", "Potwierdzono normy, podstawę prawną i zaliczenie okresu", bool)]
        self.edit_record("bonuses", self.bonus_tree, Bonus, specs, vars(Bonus()), edit)

    def edit_extra(self, edit=False):
        specs = [("name", "Nazwa własnej pozycji", None),
                 ("unit", "Jednostka", ("pp podstawy", "% emerytury", "zł miesięcznie")),
                 ("value", "Wartość", None),
                 ("indexed", "Kwota podlega wskazanej waloryzacji", bool),
                 ("enabled", "Uwzględnij w wariancie", bool)]
        self.edit_record("extras", self.extra_tree, Extra, specs, vars(Extra()), edit)

    def delete_record(self, attribute, tree):
        index = self.selected(tree)
        if index is not None:
            getattr(self.profile, attribute).pop(index)
            self.refresh_tables()
            self.changed()

    def override_years(self):
        """Lata z własną waloryzacją w kolejności widocznej w tabeli."""
        return sorted(self.profile.overrides, key=int)

    def edit_override(self, edit=False):
        index = self.selected(self.override_tree) if edit else None
        if edit and index is None:
            return
        old_year = self.override_years()[index] if edit else None
        initial = {"year": old_year or "2027", "growth": self.vars["growth"].get(),
                   "inflation": self.vars["inflation"].get()}
        if old_year:
            initial.update(self.profile.overrides[old_year])

        def accept(values):
            year = str(integer(values.pop("year"), "Rok", 2026, 2259))
            number(values["growth"], "Wzrost", maximum=Decimal(100))
            number(values["inflation"], "Inflacja", Decimal(-50), Decimal(100))
            if year in self.profile.overrides and year != old_year:
                raise ValueError("Ten rok jest już na liście. Edytuj istniejący wiersz.")
            if old_year:
                del self.profile.overrides[old_year]
            self.profile.overrides[year] = values
            self.refresh_tables()
            self.changed()

        specs = [("year", "Rok", None), ("growth", "Wzrost waloryzacyjny — %", None), ("inflation", "Inflacja — %", None)]
        Editor(self, "Zmiana wskaźników w roku", specs, initial, accept)

    def delete_override(self):
        index = self.selected(self.override_tree)
        if index is not None:
            del self.profile.overrides[self.override_years()[index]]
            self.refresh_tables()
            self.changed()

    def refresh_tables(self):
        """Przepisuje zawartość tabel z `self.profile`."""
        def yes_no(flag):
            return "tak" if flag else "nie"

        overrides = self.profile.overrides
        tables = [
            (self.pay_tree, [(a.year, a.pay, a.reference) for a in self.profile.annual_pay]),
            (self.bonus_tree, [(b.name, b.kind, b.start, b.end, yes_no(b.confirmed)) for b in self.profile.bonuses]),
            (self.extra_tree, [(e.name, e.unit, e.value, yes_no(e.indexed), yes_no(e.enabled))
                               for e in self.profile.extras]),
            (self.override_tree, [(year, overrides[year]["growth"], overrides[year]["inflation"])
                                  for year in self.override_years()]),
        ]
        for tree, rows in tables:
            tree.delete(*tree.get_children())
            for i, row in enumerate(rows):
                tree.insert("", "end", iid=str(i), values=row)

    # ------------------------------------------ reakcja na zmiany w formularzu

    def clear_results(self):
        self.result = None
        self.rows = []
        self.amount.configure(text="—")
        self.net_label.configure(text="")
        self.work_label.configure(text="")
        self.scenario_label.configure(text="")
        self.net_summary.configure(text="Oblicz emeryturę, aby zobaczyć kwotę netto.")
        self.earn_summary.configure(text="Oblicz emeryturę, aby zobaczyć skutek dorabiania.")
        self.earn_tree.delete(*self.earn_tree.get_children())
        self.forecast_tree.delete(*self.forecast_tree.get_children())
        self.chart.delete("all")

    def changed(self, *args):
        """Każda zmiana danych unieważnia wynik - nie chcemy eksportować nieaktualnych liczb."""
        if self.loading:
            return
        self.clear_results()
        self.system_label.configure(text="Dane zmienione. Oblicz ponownie.")
        self.set_result_text("")
        self.status.set("Masz niezapisane zmiany · F5: oblicz · Ctrl/Cmd+S: zapisz profil")
        self.refresh_rule_context()

    def refresh_rule_context(self):
        """Odświeża opis przepisów dla wybranej służby i systemu oraz podpowiedź o miesiącach wysługi."""
        scratch = Profile(service=self.vars["service"].get(), first_entry=self.vars["first_entry"].get(),
                          regime=self.vars["regime"].get(), new_system=self.vars["new_system"].get())
        self.rule_context.configure(text=service_rules(scratch))
        if scratch.new_system:
            group = "Wybrano: rozdział 1a, podstawa z 10 lat. Wcześniejsze przyjęcie oznacza fakultatywny wybór art. 18h."
        else:
            group = ("Wybrano: system dla przyjętych przed 1.01.2013 — 15 lat / 40%. "
                     "Odrębne warianty zależą od dokładnej daty przyjęcia.")
        self.group_context.configure(text=group)
        self.months_hint.configure(text=self.months_from_dates_hint())

    def months_from_dates_hint(self):
        """Ile pełnych miesięcy mieści się między datą przyjęcia a zwolnieniem (górna granica wysługi)."""
        try:
            first = parse_date(self.vars["first_entry"].get(), "")
            release = parse_date(self.vars["release"].get(), "")
        except ValueError:
            return ""
        if release < first:
            return ""
        months = full_months_between(first, release)
        return f"Z podanych dat wynika najwyżej {months} mies. ({months // 12} lat {months % 12} mies.)."

    def sync_system_from_date(self, *args):
        """Zmiana daty przyjęcia ustawia właściwy system (granica 1.01.2013)."""
        if self.loading:
            return
        try:
            first = parse_date(self.vars["first_entry"].get(), "Data")
        except ValueError:
            return  # data jeszcze niedokończona - czekamy
        self.vars["new_system"].set(first.year >= 2013 or self.vars["regime"].get() == "18h")
        self.refresh_rule_context()

    def sync_regime(self, *args):
        """Wybór art. 15aa / 18h ustawia przełącznik systemu."""
        if self.loading:
            return
        regime = self.vars["regime"].get()
        if regime in ("15aa", "18h"):
            self.vars["new_system"].set(regime == "18h")
        self.refresh_rule_context()

    def sync_group(self, *args):
        """Przełącznik systemu sprzeczny z wyborem 15aa/18h cofa wybór do „auto”."""
        if self.loading:
            return
        checked = self.vars["new_system"].get()
        regime = self.vars["regime"].get()
        if (checked and regime == "15aa") or (not checked and regime == "18h"):
            self.vars["regime"].set("auto")
        self.refresh_rule_context()

    # ------------------------------------------------------------------ obliczenia

    def collect(self):
        """Składa profil z bieżących wartości formularza i list trzymanych w `self.profile`."""
        profile = copy.deepcopy(self.profile)
        for key, variable in self.vars.items():
            value = variable.get()
            if key == "forecast_years":
                value = integer(value, FIELD_LABELS[key], 1, 60)
            elif key in MONTH_FIELDS:
                value = integer(value, FIELD_LABELS[key])
            setattr(profile, key, value)
        return profile

    def set_result_text(self, text):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")

    def calculate_show(self):
        """Liczy emeryturę i symulację, pokazuje wynik. Zwraca True, gdy się udało."""
        try:
            profile = self.collect()
            result = calculate(profile)
            rows = forecast(profile, result)
            effect = earnings_effect(profile, result)
            earnings_rows = earnings_table(profile, result) if result.eligible else []
        except (ValueError, TypeError) as exc:
            self.clear_results()
            self.system_label.configure(text="Sprawdź dane wejściowe")
            self.set_result_text(str(exc))
            self.status.set("Nie obliczono: " + str(exc))
            messagebox.showerror("Sprawdź dane", str(exc), parent=self)
            return False

        self.profile, self.result, self.rows = profile, result, rows
        self.amount.configure(text=format_pln(result.pension) if result.eligible else "Brak stażu")
        years, months = divmod(profile.service_months, 12)
        self.system_label.configure(
            text=f"Art. {result.regime}\nPodstawa {format_pln(result.basis)}\n"
                 f"{result.percent:.4f}% · limit {result.cap}%\nWysługa {years} lat {months} mies.")
        has_extras = result.indexed_extra or result.fixed_extra
        self.scenario_label.configure(
            text=f"Z własnymi dodatkami:\n{format_pln(result.scenario)} / mies." if has_extras else "")

        details = "SKŁADNIKI PROCENTOWE\n\n"
        details += "\n".join(f"{label}: {value:.4f} pp" for label, value in result.breakdown)
        details += "\n\nZAŁOŻENIA I UWAGI\n\n" + "\n\n".join(result.warnings)
        self.set_result_text(details)
        self.show_net_and_earnings(profile, result, effect, earnings_rows)

        self.forecast_tree.delete(*self.forecast_tree.get_children())
        for row in rows:
            self.forecast_tree.insert("", "end", values=(
                row.year, str(row.rate), format_pln(row.december), format_pln(row.legal_december),
                format_pln(row.real_december), format_pln(row.net_december), format_pln(row.annual),
                format_pln(row.cumulative)))
        self.draw_chart()
        self.status.set(f"Obliczono · reguły sprawdzone {RULE_DATE} · wartości brutto · profil: {profile.name}")
        return True

    def show_net_and_earnings(self, profile, result, effect, earnings_rows):
        """Wypełnia panel wyniku i zakładkę „Netto i dorabianie” po udanym obliczeniu."""
        self.earn_tree.delete(*self.earn_tree.get_children())
        self.net_label.configure(text="")
        self.work_label.configure(text="")
        if not result.eligible:
            self.net_summary.configure(text="Brak stażu — nie ma emerytury do wyliczenia.")
            self.earn_summary.configure(text="Brak stażu — nie ma emerytury do zmniejszenia.")
            return

        net = net_pension(result.pension, profile.pit2)
        self.net_label.configure(text=f"Netto: {format_pln(net.net)}")
        summary = (f"Emerytura brutto:  {format_pln(net.gross)}\n"
                   f"− składka zdrowotna 9%:  {format_pln(net.health)}\n"
                   f"− zaliczka na PIT:  {format_pln(net.tax)}\n"
                   f"= na rękę:  {format_pln(net.net)} miesięcznie")
        if result.indexed_extra or result.fixed_extra:
            variant = net_pension(result.scenario, profile.pit2)
            summary += (f"\n\nWariant z własnymi dodatkami: {format_pln(variant.gross)} brutto, "
                        f"{format_pln(variant.net)} netto.")
        self.net_summary.configure(text=summary)

        # Skutek dorabiania.
        limits = (f"Progi: 70% = {format_pln(effect.low)}, 130% = {format_pln(effect.high)}.")
        if effect.exempt:
            verdict = "Emerytura wynosi co najmniej 75% podstawy — dorabiasz bez zmniejszeń."
        elif effect.zone == "below":
            verdict = (f"Przychód {format_pln(effect.income)} nie przekracza progu 70%. "
                       "Emerytura nie jest zmniejszana.")
        else:
            reason = ("Przychód między 70% a 130%: zmniejszenie o kwotę przekroczenia (z ograniczeniami)."
                      if effect.zone == "reduced" else "Przychód powyżej 130%: zmniejszenie o 25% emerytury.")
            lost_net = effect.net_before.net - effect.net_after.net
            verdict = (f"{reason}\nEmerytura zmniejszona o {format_pln(effect.reduction)} → "
                       f"{format_pln(effect.pension_after)} brutto, {format_pln(effect.net_after.net)} netto "
                       f"(tracisz {format_pln(lost_net)} netto miesięcznie).")
            self.work_label.configure(
                text=f"Dorabianie: −{format_pln(effect.reduction)} → {format_pln(effect.pension_after)} brutto")
        notes = "\n".join("• " + warning for warning in effect.warnings)
        self.earn_summary.configure(text=f"{verdict}\n{limits}\n\n{notes}")
        for income, reduction, after, net_after in earnings_rows:
            self.earn_tree.insert("", "end", values=(format_pln(income), format_pln(reduction),
                                                      format_pln(after), format_pln(net_after)))

    def draw_chart(self):
        """Wykres miesięcznej (grudniowej) emerytury w kolejnych latach; linie wybiera użytkownik."""
        canvas = self.chart
        canvas.delete("all")
        if not self.result or not self.rows:
            return

        width = max(canvas.winfo_width(), 500)
        left, top, bottom, right = 78, 22, 214, width - 26
        series = [(color, [float(getattr(row, attribute)) for row in self.rows])
                  for attribute, _, color, _ in CHART_SERIES if self.chart_vars[attribute].get()]
        if not series:
            canvas.create_text(width / 2, 110, text="Zaznacz co najmniej jedną linię, aby zobaczyć wykres.",
                               fill=MUTED, font=(FONT, 12))
            return
        canvas.create_text(left, 8, text="Miesięczna emerytura w grudniu, zł", anchor="w", fill=MUTED,
                           font=(FONT, 10))
        highest = max(max(values) for _, values in series) * 1.12 or 1

        # Siatka z opisem osi pionowej.
        for i in range(5):
            y = top + (bottom - top) * i / 4
            canvas.create_line(left, y, right, y, fill=LINE)
            canvas.create_text(left - 10, y, text=f"{highest * (1 - i / 4):,.0f}".replace(",", " "),
                               anchor="e", fill=MUTED, font=(FONT, 10))

        # Linie rysujemy od końca, żeby pierwsza z wybranych (wariant) leżała na wierzchu.
        count = len(self.rows)
        for color, values in reversed(series):
            points = []
            for i, value in enumerate(values):
                points.append(left + (right - left) * i / max(1, count - 1))
                points.append(bottom - (bottom - top) * value / highest)
            if count > 1:
                canvas.create_line(*points, fill=color, width=2.5)
            else:  # przy jednym roku linia byłaby niewidoczna - rysujemy kropkę
                x, y = points
                canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color, outline=color)

        # Opis osi poziomej: pierwszy, środkowy i ostatni rok.
        for i in sorted({0, count // 2, count - 1}):
            x = left + (right - left) * i / max(1, count - 1)
            canvas.create_text(x, bottom + 20, text=str(self.rows[i].year), fill=MUTED, font=(FONT, 10))

    # ------------------------------------------------------------ pliki i profile

    def fill_profile(self, profile):
        """Wstawia profil do formularza i od razu przelicza."""
        self.loading = True
        self.profile = profile
        for key, variable in self.vars.items():
            if key == "new_system":
                # Profil bez wyboru (None) ustawia przełącznik według daty przyjęcia.
                variable.set(profile.new_system if profile.new_system is not None
                             else "18e" in calculate(profile).regime)
            else:
                variable.set(getattr(profile, key))
        self.refresh_tables()
        self.loading = False
        self.refresh_rule_context()
        self.calculate_show()

    def open_profile(self):
        path = filedialog.askopenfilename(parent=self, title="Otwórz profil EMKA", filetypes=[("Profil JSON", "*.json")])
        if not path:
            return
        try:
            profile = load_profile(path)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Nie otwarto profilu", str(exc), parent=self)
            return
        self.fill_profile(profile)
        self.status.set("Otworzono: " + path)

    def write_file(self, action, path):
        """Wykonuje zapis i pokazuje komunikat o powodzeniu albo błędzie."""
        try:
            action()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Nie zapisano pliku", str(exc), parent=self)
            return
        self.status.set("Zapisano: " + path)

    def save(self):
        if not self.calculate_show():
            return
        path = filedialog.asksaveasfilename(parent=self, title="Zapisz profil", defaultextension=".json",
                                            initialfile="emka-profil.json", filetypes=[("Profil JSON", "*.json")])
        if path:
            self.write_file(lambda: save_profile(path, self.profile), path)

    def csv(self):
        if not self.calculate_show():
            return
        path = filedialog.asksaveasfilename(parent=self, title="Eksport symulacji", defaultextension=".csv",
                                            initialfile="emka-waloryzacja.csv", filetypes=[("Tabela CSV", "*.csv")])
        if path:
            self.write_file(lambda: export_csv(path, self.profile, self.result), path)

    def export_report(self):
        if not self.calculate_show():
            return
        path = filedialog.asksaveasfilename(parent=self, title="Raport z pełną konfiguracją", defaultextension=".md",
                                            initialfile="emka-raport.md", filetypes=[("Raport Markdown", "*.md")])
        if path:
            self.write_file(lambda: Path(path).write_text(report(self.profile, self.result), encoding="utf-8"), path)

    # --------------------------------------------------------------- porównanie

    def add_snapshot(self):
        if not self.calculate_show():
            return
        self.snapshots.append(copy.deepcopy(self.profile))
        self.refresh_comparison()
        self.status.set("Dodano niezależną kopię wyniku do zakładki Porównanie.")

    def refresh_comparison(self):
        self.compare_tree.delete(*self.compare_tree.get_children())
        for i, profile in enumerate(self.snapshots):
            result = calculate(profile)
            rows = forecast(profile, result)
            last_year = f"{rows[-1].year}: {format_pln(rows[-1].december)}" if rows else "Brak stażu"
            self.compare_tree.insert("", "end", iid=str(i), values=(
                profile.name, profile.service, result.regime, format_pln(result.pension),
                format_pln(result.scenario), last_year))

    def show_snapshot_rules(self, event=None):
        index = self.selected(self.compare_tree)
        if index is not None:
            self.compare_rules.configure(text=service_rules(self.snapshots[index]))

    def delete_snapshot(self):
        index = self.selected(self.compare_tree)
        if index is not None:
            self.snapshots.pop(index)
            self.refresh_comparison()

    def restore_snapshot(self):
        index = self.selected(self.compare_tree)
        if index is not None:
            self.fill_profile(copy.deepcopy(self.snapshots[index]))


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
