from __future__ import annotations

import asyncio
from functools import partial
from pathlib import Path
from typing import List

from pyflowlauncher import Plugin, Result, api

from launcher import KEEP_OPEN, TenorLauncher
from tenor import GIF, Tenor

ICON = str(Path(__file__).resolve().parent.parent / "icon.png")
TRENDING_TERMS = 10
PREVIEW_FORMAT = "tinygif"
OPEN_WEBSITE = "open website"

plugin = Plugin(launcher=TenorLauncher())


def tenor(api_key: str) -> Tenor:
    return Tenor(api_key)


async def run_blocking(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args))


@plugin.on_method
async def query(query: str):
    settings = plugin.settings
    api_key = settings["api_key"]
    max_results = settings["max_results"]
    default_action = settings["default_action"]
    if api_key == "":
        return [Result(
            title="Please set your API key in the settings.",
            icon=ICON,
        ).add_action(api.open_setting_dialog())]
    client = tenor(api_key)
    if query == "":
        terms = await run_blocking(client.trending_terms, TRENDING_TERMS)
        return [trending_result(term) for term in terms]
    gifs = await run_blocking(client.search, query, max_results)
    icons = await run_blocking(client.download_all, gifs, PREVIEW_FORMAT)
    return [gif_result(gif, icon, default_action) for gif, icon in zip(gifs, icons)]


def trending_result(term: str) -> Result:
    return Result(
        title=term,
        subtitle="Select to search with this query",
        icon=ICON,
    ).add_action(search_term, [term])


def gif_result(gif: GIF, icon: Path, default_action: str) -> Result:
    return Result(
        title=gif.content_description,
        subtitle=f"Select to {default_action.lower()}.",
        icon=str(icon),
        context_data=[gif.data],
        copy_text=gif.url,
    ).add_action(default_command(default_action, gif.url))


def default_command(default_action: str, url: str):
    if default_action.lower() == OPEN_WEBSITE:
        return api.open_url(url)
    return api.copy_to_clipboard(url)


@plugin.on_method
def context_menu(data) -> List[Result]:
    gif = GIF(data[0])
    return [
        Result(
            title="Open in Browser",
            subtitle="Open GIF on tenor's website.",
            icon=ICON,
        ).add_action(api.open_url(gif.item_url)),
        Result(
            title="Copy URL to clipboard",
            subtitle="Copy GIF URL to clipboard.",
            icon=ICON,
        ).add_action(api.copy_to_clipboard(gif.url)),
    ]


@plugin.on_method
async def search_term(term: str):
    keyword = plugin.launcher.action_keyword
    text = f"{keyword} {term} " if keyword else f"{term} "
    await plugin.launcher.api.invoke(api.change_query(text, True))
    return KEEP_OPEN
