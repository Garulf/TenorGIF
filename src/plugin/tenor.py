from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Dict, List

import requests

BASE_URL = "https://tenor.googleapis.com/v2"
DOWNLOAD_WORKERS = 20


class TenorError(Exception):
    pass


def describe(error: requests.RequestException) -> str:
    response = getattr(error, "response", None)
    if response is None:
        return str(error)
    try:
        message = response.json()["error"]["message"]
    except (ValueError, KeyError, TypeError):
        return str(error)
    return f"{response.status_code}: {message}"


def checked(response: Any) -> Any:
    try:
        response.raise_for_status()
    except requests.RequestException as error:
        raise TenorError(describe(error)) from error
    return response


class GIF:

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data

    @property
    def id(self) -> str:
        return self.data["id"]

    @property
    def content_description(self) -> str:
        return self.data["content_description"]

    @property
    def item_url(self) -> str:
        return self.data["itemurl"]

    @property
    def url(self) -> str:
        return self.media("gif")["url"]

    def media(self, gif_format: str) -> Dict[str, Any]:
        return self.data["media_formats"][gif_format]


class Tenor:

    def __init__(self, api_key: str, http: Any = requests) -> None:
        self.api_key = api_key
        self.http = http

    def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params["key"] = self.api_key
        return checked(self._get(f"{BASE_URL}/{endpoint}", params=params)).json()

    def _get(self, url: str, **kwargs: Any) -> Any:
        try:
            return self.http.get(url, **kwargs)
        except requests.RequestException as error:
            raise TenorError(describe(error)) from error

    def search(self, query: str, limit: int = 10) -> List[GIF]:
        results = self._request("search", {"q": query, "limit": limit})["results"]
        return [GIF(result) for result in results]

    def trending_terms(self, limit: int = 10) -> List[str]:
        return list(self._request("trending_terms", {"limit": limit})["results"])

    def download(self, gif: GIF, gif_format: str) -> Path:
        url = gif.media(gif_format)["url"]
        path = Path(gettempdir(), f"{gif.id}.{url.split('.')[-1]}")
        if not path.exists():
            self._download(url, path)
        return path

    def download_all(self, gifs: List[GIF], gif_format: str) -> List[Path]:
        with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
            return list(executor.map(lambda gif: self.download(gif, gif_format), gifs))

    def _download(self, url: str, path: Path) -> None:
        response = checked(self._get(url, stream=True))
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
