import pytest
import requests

from conftest import FakeResponse
from tenor import BASE_URL, TenorError


def test_search_sends_query_limit_and_key(client, http):
    gifs = client.search("dog", 15)
    assert http.calls == [(f"{BASE_URL}/search", {"q": "dog", "limit": 15, "key": "test-key"})]
    assert [gif.content_description for gif in gifs] == ["Happy dog dancing", "Dog wagging tail"]
    assert gifs[0].url == "https://media.tenor.com/1001/full.gif"
    assert gifs[0].item_url == "https://tenor.com/view/1001"


def test_trending_terms(client, http):
    assert client.trending_terms(10) == ["good morning", "happy friday", "thank you"]
    assert http.calls == [(f"{BASE_URL}/trending_terms", {"limit": 10, "key": "test-key"})]


def test_download_saves_to_temp_dir_once(client, http, temp_dir):
    gif = client.search("dog")[0]
    http.calls.clear()
    path = client.download(gif, "tinygif")
    assert path == temp_dir / "1001.gif"
    assert path.read_bytes() == b"GIF89a"
    client.download(gif, "tinygif")
    assert http.calls == [("https://media.tenor.com/1001/tiny.gif", {})]


def test_download_all_keeps_result_order(client, temp_dir):
    gifs = client.search("dog")
    assert client.download_all(gifs, "tinygif") == [temp_dir / "1001.gif", temp_dir / "1002.gif"]


def test_http_error_uses_tenor_error_message(client, http):
    http.error = FakeResponse({"error": {"code": 403, "message": "Permission denied on the service."}}, status=403)
    with pytest.raises(TenorError, match="^403: Permission denied on the service.$"):
        client.search("dog")


def test_http_error_without_json_body(client, http):
    http.error = FakeResponse(None, status=500)
    with pytest.raises(TenorError, match="500 Client Error"):
        client.trending_terms()


def test_connection_error(client, http):
    http.error = requests.ConnectionError("Max retries exceeded")
    with pytest.raises(TenorError, match="Max retries exceeded"):
        client.search("dog")
