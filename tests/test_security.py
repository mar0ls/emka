"""Testy wynikające z analizy STRIDE (docs/STRIDE.md): program nie łączy się z siecią i nie wykonuje cudzego kodu."""
import ast
import re
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "emka"

# Moduły, które pozwalałyby wysłać dane na zewnątrz albo uruchomić obcy kod.
FORBIDDEN_IMPORTS = {"socket", "ssl", "http", "urllib", "ftplib", "smtplib", "telnetlib", "requests", "xmlrpc",
                     "subprocess", "pickle", "marshal", "shelve", "ctypes", "importlib", "runpy", "code"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__"}


def sources():
    return {path: ast.parse(path.read_text(encoding="utf-8"), filename=str(path)) for path in PACKAGE.glob("*.py")}


class NoNetworkNoCodeExecutionTests(unittest.TestCase):
    def test_package_has_python_files(self):
        self.assertGreaterEqual(len(sources()), 5)

    def test_no_network_or_process_modules_imported(self):
        for path, tree in sources().items():
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                for name in names:
                    self.assertNotIn(name.split(".")[0], FORBIDDEN_IMPORTS, f"{path.name}: import {name}")

    def test_no_dynamic_code_execution(self):
        for path, tree in sources().items():
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, FORBIDDEN_CALLS, f"{path.name}:{node.lineno}: {node.func.id}()")
                if isinstance(node, ast.Attribute) and node.attr in {"system", "popen", "loads"} and \
                        isinstance(node.value, ast.Name) and node.value.id in {"os", "pickle", "marshal"}:
                    self.fail(f"{path.name}:{node.lineno}: {node.value.id}.{node.attr}")

    def test_only_browser_is_opened_with_https_addresses(self):
        for path, tree in sources().items():
            text = path.read_text(encoding="utf-8")
            for url in re.findall(r"https?://[^\s\"')]+", text):
                self.assertTrue(url.startswith("https://"), f"{path.name}: {url}")

    def test_markdown_links_in_regulations_are_https(self):
        text = (PACKAGE / "PRZEPISY.md").read_text(encoding="utf-8")
        for url in re.findall(r"\]\((\S+?)\)", text):
            self.assertTrue(url.startswith("https://"), url)


if __name__ == "__main__":
    unittest.main()
