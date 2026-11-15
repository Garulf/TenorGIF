import json

import pytest
import requests

import tenor as tenor_module
import tenorgif
from tenor import Tenor


def gif_data(gif_id, description):
    return {
        "id": gif_id,
        "content_description": description,
        "itemurl": f"https://tenor.com/view/{gif_id}",
        "media_formats": {
            "gif": {"url": f"https://media.tenor.com/{gif_id}/full.gif"},
            "tinygif": {"url": f"https://media.tenor.com/{gif_id}/tiny.gif"},
        },
    }


SEARCH = {"results": [gif_data("1001", "Happy dog dancing"), gif_data("1002", "Dog wagging tail")]}
TRENDING_TERMS = {"results": ["good morning", "happy friday", "thank you"]}
PAYLOADS = {"search": SEARCH, "trending_terms": TRENDING_TERMS}


class FakeResponse:
    def __init__(self, payload=None, status=200, content=b"GIF89a"):
        self._payload = payload
        self.status_code = status
        self.content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error", response=self)

    def json(self):
        return json.loads(json.dumps(self._payload))

    def iter_content(self, chunk_size=1024):
        yield self.content


class FakeHttp:
    def __init__(self):
        self.calls = []
        self.error = None

    def get(self, url, params=None, stream=False):
        self.calls.append((url, dict(params or {})))
        if self.error is not None:
            return self.error
        if url.startswith(tenor_module.BASE_URL):
            return FakeResponse(PAYLOADS[url.rsplit("/", 1)[-1]])
        return FakeResponse()


@pytest.fixture(autouse=True)
def temp_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(tenor_module, "gettempdir", lambda: str(tmp_path))
    return tmp_path


@pytest.fixture
def http():
    return FakeHttp()


@pytest.fixture
def client(http):
    return Tenor("test-key", http=http)


@pytest.fixture
def settings(client, monkeypatch):
    launcher = tenorgif.plugin.launcher
    launcher._settings = {"api_key": "test-key", "max_results": "10", "default_action": "Copy to Clipboard"}
    launcher.action_keyword = "tg"
    monkeypatch.setattr(tenorgif, "tenor", lambda api_key: client)
    yield launcher._settings
    launcher._settings = {}
    launcher.action_keyword = ""
