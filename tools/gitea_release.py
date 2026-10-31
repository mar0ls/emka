"""Dołącza pliki do wydania w Gitei (tworzy wydanie dla tagu, jeśli jeszcze go nie ma).

    python tools/gitea_release.py PLIK_LUB_WZORZEC [...]

Każde zadanie CI wywołuje to dla własnych plików, więc wydanie nie czeka na wszystkie systemy naraz.
Do każdego pliku dokłada `<nazwa>.sha256`. Korzysta ze zmiennych, które ustawia Gitea Actions:
GITHUB_SERVER_URL, GITHUB_REPOSITORY, GITHUB_REF_NAME oraz GITEA_TOKEN (albo GITHUB_TOKEN).
Tylko biblioteka standardowa. NIE BYŁO JESZCZE URUCHAMIANE na prawdziwej instancji Gitei.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class GiteaApi:
    def __init__(self, server, repository, token):
        self.base = f"{server.rstrip('/')}/api/v1/repos/{repository}"
        self.token = token

    def request(self, method, path, body=None, content_type="application/json"):
        data = body if isinstance(body, bytes) else (json.dumps(body).encode() if body is not None else None)
        request = urllib.request.Request(self.base + path, data=data, method=method)
        request.add_header("Authorization", f"token {self.token}")
        if data is not None:
            request.add_header("Content-Type", content_type)
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read()
        return json.loads(raw) if raw else {}

    def find_release(self, tag):
        try:
            return self.request("GET", f"/releases/tags/{urllib.parse.quote(tag)}")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                error.close()
                return None
            raise

    def get_or_create_release(self, tag, title, notes):
        release = self.find_release(tag)
        if release:
            return release
        try:
            return self.request("POST", "/releases", {"tag_name": tag, "name": title, "body": notes,
                                                      "draft": False, "prerelease": "-" in tag})
        except urllib.error.HTTPError:
            # Inne zadanie mogło utworzyć to samo wydanie chwilę wcześniej.
            release = self.find_release(tag)
            if release:
                return release
            raise

    def upload(self, release_id, name, content):
        boundary = uuid.uuid4().hex
        head = (f'--{boundary}\r\nContent-Disposition: form-data; name="attachment"; filename="{name}"\r\n'
                "Content-Type: application/octet-stream\r\n\r\n").encode()
        body = head + content + f"\r\n--{boundary}--\r\n".encode()
        query = urllib.parse.urlencode({"name": name})
        self.request("POST", f"/releases/{release_id}/assets?{query}", body,
                     content_type=f"multipart/form-data; boundary={boundary}")


def release_notes():
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "release.py"), "notes"],
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


def publish(api, tag, files, notes):
    release = api.get_or_create_release(tag, f"EMKA {tag.lstrip('v')}", notes)
    for path in map(Path, files):
        content = path.read_bytes()
        api.upload(release["id"], path.name, content)
        checksum = f"{hashlib.sha256(content).hexdigest()}  {path.name}\n".encode()
        api.upload(release["id"], path.name + ".sha256", checksum)
        print("Dołączono:", path.name)


def main(patterns):
    # Powłoka Windows nie rozwija `*`, więc robimy to sami.
    files = sorted(path for pattern in patterns for path in glob.glob(pattern) if Path(path).is_file())
    if not files:
        print(__doc__, file=sys.stderr)
        return 2
    token = os.environ.get("GITEA_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("BŁĄD: brak GITEA_TOKEN / GITHUB_TOKEN.", file=sys.stderr)
        return 1
    api = GiteaApi(os.environ["GITHUB_SERVER_URL"], os.environ["GITHUB_REPOSITORY"], token)
    publish(api, os.environ["GITHUB_REF_NAME"], files, release_notes())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
