"""Testy narzędzi wydania: wersja, CHANGELOG, sumy kontrolne, skrypt Gitei i zasady workflow."""
import contextlib
import http.server
import importlib.util
import io
import json
import re
import tempfile
import threading
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load_tool("release")
gitea_release = load_tool("gitea_release")


class VersionTests(unittest.TestCase):
    def test_version_is_semver_and_single_source(self):
        self.assertRegex(release.read_version(), release.VERSION_PATTERN)
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertNotRegex(pyproject, r'(?m)^version\s*=\s*"\d', "wersja ma być tylko w emka/__init__.py")
        self.assertIn("emka.__version__", pyproject)

    def test_changelog_describes_current_version(self):
        self.assertTrue(release.changelog_section(release.read_version()))

    def test_check_tag(self):
        version = release.read_version()
        self.assertEqual(release.check_tag(f"v{version}"), [])
        self.assertTrue(release.check_tag("v99.0.0"))
        self.assertTrue(release.check_tag(version))  # bez przedrostka "v"

    def test_changelog_section_stops_at_next_heading(self):
        text = "# Historia\n\n## [0.2.0] - x\nnowe\n\n## [0.1.0] - y\nstare\n"
        self.assertEqual(release.changelog_section("0.2.0", text), "nowe")
        self.assertEqual(release.changelog_section("0.1.0", text), "stare")
        self.assertIsNone(release.changelog_section("0.3.0", text))

    def test_license_is_mit(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("MIT License"))
        self.assertIn("Copyright (c) 2026", text)

    def test_checksums_match_sha256sum_format(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "a.bin").write_bytes(b"abc")
            lines = release.write_checksums(folder)
            self.assertEqual(lines, ["ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad  a.bin"])
            self.assertTrue((Path(folder) / "SHA256SUMS").exists())
            # Ponowne wywołanie nie dolicza własnego pliku z sumami.
            self.assertEqual(release.write_checksums(folder), lines)


class WorkflowTests(unittest.TestCase):
    """Zasady z analizy STRIDE (Tampering/Elevation w łańcuchu dostaw) sprawdzane automatycznie."""

    def workflow_files(self):
        return sorted((ROOT / ".github" / "workflows").glob("*.yml")) + [ROOT / ".gitea" / "workflows" / "build.yml"]

    def test_checkout_and_setup_actions_are_pinned_to_commit(self):
        for path in self.workflow_files():
            for action in re.findall(r"uses:\s*(actions/(?:checkout|setup-python)@\S+)", path.read_text(encoding="utf-8")):
                self.assertRegex(action, r"@[0-9a-f]{40}$", f"{path.name}: {action} nie jest przypięta do skrótu")

    def test_github_workflow_has_least_privilege(self):
        text = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^permissions:\n  contents: read")
        self.assertEqual(text.count("contents: write"), 1, "prawo zapisu tylko w zadaniu release")
        self.assertNotIn("pull_request_target", text)

    def test_test_workflow_cannot_write_or_publish(self):
        text = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^permissions:\n  contents: read")
        self.assertNotIn("contents: write", text)
        self.assertNotIn("gh release", text)
        self.assertNotIn("pull_request_target", text)

    def test_law_watch_can_only_open_issues(self):
        text = (ROOT / ".github" / "workflows" / "przepisy.yml").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^permissions:\n  contents: read")
        self.assertIn("issues: write", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("gh release", text)
        self.assertNotIn("git push", text)
        self.assertNotIn("pull_request_target", text)
        self.assertRegex(text, r'cron: "\d+ \d+ \d+ \* \*"')  # raz w miesiącu

    def test_release_only_on_tags(self):
        text = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
        self.assertIn("if: startsWith(github.ref, 'refs/tags/')", text)

    def test_checksums_cover_only_programs(self):
        text = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
        self.assertLess(text.index("release.py checksums"), text.index("cp LICENSE"))

    def test_build_dependency_is_pinned(self):
        requirements = (ROOT / "tools" / "requirements-build.txt").read_text(encoding="utf-8")
        self.assertRegex(requirements, r"(?m)^pyinstaller==\d+\.\d+")


class FakeGitea(http.server.BaseHTTPRequestHandler):
    releases = {}
    assets = []

    def log_message(self, *args):
        pass

    def reply(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        tag = self.path.rsplit("/", 1)[-1]
        if self.headers["Authorization"] != "token secret":
            return self.reply(401, {})
        release = self.releases.get(tag)
        self.reply(200 if release else 404, release or {})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        if self.path.endswith("/releases"):
            data = json.loads(body)
            self.releases[data["tag_name"]] = {"id": 7, **data}
            return self.reply(201, self.releases[data["tag_name"]])
        self.assets.append((self.path, body))
        self.reply(201, {})


class GiteaReleaseTests(unittest.TestCase):
    def setUp(self):
        FakeGitea.releases, FakeGitea.assets = {}, []
        self.server = http.server.HTTPServer(("127.0.0.1", 0), FakeGitea)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.api = gitea_release.GiteaApi(f"http://127.0.0.1:{self.server.server_port}", "master/emka", "secret")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_creates_release_once_and_uploads_file_with_checksum(self):
        with tempfile.TemporaryDirectory() as folder:
            program = Path(folder) / "EMKA-0.1.0-linux-x86_64"
            program.write_bytes(b"program")
            with contextlib.redirect_stdout(io.StringIO()):
                gitea_release.publish(self.api, "v0.1.0", [program], "opis")
                gitea_release.publish(self.api, "v0.1.0", [program], "opis")  # drugie zadanie CI, to samo wydanie
        self.assertEqual(list(FakeGitea.releases), ["v0.1.0"])
        self.assertEqual(FakeGitea.releases["v0.1.0"]["name"], "EMKA 0.1.0")
        self.assertFalse(FakeGitea.releases["v0.1.0"]["prerelease"])
        paths = [path for path, _ in FakeGitea.assets]
        self.assertIn("/api/v1/repos/master/emka/releases/7/assets?name=EMKA-0.1.0-linux-x86_64", paths)
        self.assertIn("/api/v1/repos/master/emka/releases/7/assets?name=EMKA-0.1.0-linux-x86_64.sha256", paths)
        self.assertTrue(any(b"program" in body for _, body in FakeGitea.assets))

    def test_wrong_token_is_rejected(self):
        api = gitea_release.GiteaApi(self.api.base.split("/api/")[0], "master/emka", "zly")
        with self.assertRaises(urllib.error.HTTPError) as caught:
            api.find_release("v0.1.0")
        self.assertEqual(caught.exception.code, 401)
        caught.exception.close()


if __name__ == "__main__":
    unittest.main()
