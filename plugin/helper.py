import sys
import os
import json
from pathlib import Path
from tempfile import gettempdir
from concurrent.futures import ThreadPoolExecutor

import requests

BASE_URL = "https://api.tenor.com/v1"
plugindir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(plugindir)
sys.path.append(os.path.join(plugindir, "lib"))
sys.path.append(os.path.join(plugindir, "plugin"))

class TenorBase(object):

    def _request(self, endpoint: str, params: dict) -> dict:
        params["key"] = self.API_KEY
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response

class Tenor(TenorBase):

    def __init__(self, API_KEY):
        self.API_KEY = API_KEY

    def search(self, query: str, limit: int = 10) -> dict:
        params = {
            "q": query,
            "limit": limit,
        }
        results = self._request("search", params).json()['results']
        gifs = []
        for result in results:
            gifs.append(
                GIF(result)
            )
        return Results(gifs)

    def trending_gifs(self, limit: int = 10) -> dict:
        params = {
            "limit": limit,
        }
        results = self._request("trending", params).json()['results']
        gifs = []
        for result in results:
            gifs.append(
                GIF(result)
            )
        return gifs

    def trending_terms(self, limit: int = 10) -> dict:
        params = {
            "limit": limit,
        }
        results = self._request("trending_terms", params).json()['results']
        terms = []
        for result in results:
            terms.append(
                result
            )
        return terms

class Results():

    def __init__(self, results: list):
        self._results = results

    def __iter__(self):
        return iter(self._results)

    def download_all(self, gif_format: str = "tinygif",
                     max_workers: int = 20):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for gif in self._results:
                executor.submit(gif.download, gif_format)

class GIF(TenorBase):

    def __init__(self, data: dict):
        self._data = data
        self.__dict__.update(data)
        for item in data['media'][0]:
            self.__setattr__(item, data['media'][0][item])

    def _download(self, url: str, path: str) -> None:
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def download(self, gif_format:str, preview=False) -> str:

        media_object = self.__getattribute__(gif_format)
        url = media_object['url']
        if preview:
            url = media_object['preview']
        file_ext = url.split(".")[-1]
        path = Path(gettempdir(), f"{self.id}.{file_ext}")
        if not path.exists():
            self._download(url, path)
        return path