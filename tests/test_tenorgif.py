import asyncio

import tenorgif
from conftest import FakeResponse
from launcher import KEEP_OPEN


def run_query(text):
    return [result.to_json() for result in asyncio.run(tenorgif.query(text))]


def test_missing_api_key_opens_settings(settings):
    settings["api_key"] = ""
    (result,) = run_query("dog")
    assert result["Title"] == "Please set your API key in the settings."
    assert result["JsonRPCAction"]["Method"] == "Flow.Launcher.OpenSettingDialog"


def test_empty_query_lists_trending_terms(settings):
    results = run_query("")
    assert [r["Title"] for r in results] == ["good morning", "happy friday", "thank you"]
    assert results[0]["SubTitle"] == "Select to search with this query"
    assert results[0]["JsonRPCAction"]["Method"] == "search_term"
    assert results[0]["JsonRPCAction"]["Parameters"] == ["good morning"]


def test_search_returns_gifs_with_downloaded_icons(settings, http, temp_dir):
    results = run_query("dog")
    assert http.calls[0][1] == {"q": "dog", "limit": "10", "key": "test-key"}
    assert [r["Title"] for r in results] == ["Happy dog dancing", "Dog wagging tail"]
    first = results[0]
    assert first["SubTitle"] == "Select to copy to clipboard."
    assert first["IcoPath"] == str(temp_dir / "1001.gif")
    assert first["CopyText"] == "https://media.tenor.com/1001/full.gif"
    assert first["JsonRPCAction"]["Method"] == "Flow.Launcher.CopyToClipboard"
    assert first["JsonRPCAction"]["Parameters"][0] == "https://media.tenor.com/1001/full.gif"


def test_open_website_default_action(settings):
    settings["default_action"] = "Open website"
    first = run_query("dog")[0]
    assert first["SubTitle"] == "Select to open website."
    assert first["JsonRPCAction"]["Method"] == "Flow.Launcher.OpenUrl"
    assert first["JsonRPCAction"]["Parameters"][0] == "https://media.tenor.com/1001/full.gif"


def test_context_menu_opens_page_and_copies_url(settings):
    context = run_query("dog")[0]["ContextData"]
    menu = [r.to_json() for r in tenorgif.context_menu(context)]
    assert [r["Title"] for r in menu] == ["Open in Browser", "Copy URL to clipboard"]
    assert menu[0]["JsonRPCAction"]["Method"] == "Flow.Launcher.OpenUrl"
    assert menu[0]["JsonRPCAction"]["Parameters"][0] == "https://tenor.com/view/1001"
    assert menu[1]["JsonRPCAction"]["Method"] == "Flow.Launcher.CopyToClipboard"
    assert menu[1]["JsonRPCAction"]["Parameters"][0] == "https://media.tenor.com/1001/full.gif"


def test_search_term_changes_query_and_keeps_window_open(settings, monkeypatch):
    sent = []

    async def invoke(command):
        sent.append(command)

    monkeypatch.setattr(tenorgif.plugin.launcher.api, "invoke", invoke)
    assert asyncio.run(tenorgif.search_term("good morning")) == KEEP_OPEN
    assert sent == [{"Method": "Flow.Launcher.ChangeQuery", "Parameters": ["tg good morning ", True]}]


def test_missing_settings_ask_for_api_key(settings):
    settings.clear()
    (result,) = run_query("dog")
    assert result["Title"] == "Please set your API key in the settings."


def test_missing_optional_settings_use_template_defaults(settings, http):
    del settings["max_results"]
    del settings["default_action"]
    first = run_query("dog")[0]
    assert http.calls[0][1]["limit"] == 10
    assert first["SubTitle"] == "Select to copy to clipboard."


def test_rejected_request_is_shown_as_a_result(settings, http):
    http.error = FakeResponse({"error": {"code": 403, "message": "Permission denied on the service."}}, status=403)
    (result,) = run_query("dog")
    assert result["Title"] == "Tenor request failed"
    assert result["SubTitle"] == "403: Permission denied on the service."
    assert result["JsonRPCAction"]["Method"] == "Flow.Launcher.OpenSettingDialog"
