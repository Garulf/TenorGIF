import sys
import webbrowser
import json

from flox import Flox

from helper import Tenor


class TenorFlow(Flox):


    def query(self, query):

        api_key = self.settings["api_key"]
        max_results = self.settings["max_results"]
        default_action = self.settings["default_action"]
        if api_key == "":
            self.add_item(
                title="Please set your API key in the settings.",
                method=self.open_setting_dialog,
                parameters=[]
            )
            return
        t = Tenor(api_key)
        if query == "":
            results = t.trending_terms(10)
            for term in results:
                self.add_item(
                    title=term,
                    subtitle="Select to search with this query",
                    icon="icon.png",
                    method=self.search_term,
                    parameters=[term],
                    dont_hide=True
                )
            return
        else:
            results = t.search(query, max_results)
            results.download_all()
        for result in results:
            self.add_item(
                title=result.content_description,
                subtitle=f"Select to {default_action.lower()}.",
                icon=str(result.download('tinygif')),
                method=self.activate,
                parameters=[default_action, result.gif["url"]],
                context=[result._data]
            )

    def context_menu(self, data):
        self.add_item(
            title="Open in Browser",
            subtitle="Open GIF on tenor's website.",
            icon="icon.png",
            method=self.open_in_browser,
            parameters=[data[0]["itemurl"]]
        )
        self.add_item(
            title="Copy URL to clipboard",
            subtitle="Copy GIF URL to clipboard.",
            icon="icon.png",
            method=self.copy_to_clipboard,
            parameters=[data[0]["media_formats"]["gif"]["url"]]
        )

    def activate(self, default_action, url):
        if default_action.lower() == "open website":
            webbrowser.open(url)
        elif default_action.lower() == "copy to clipboard":
            print(json.dumps({"method": "Flow.Launcher.CopyToClipboard","parameters":[url]}))

    def search_term(self, term):
        self.change_query(F"{self.user_keyword} {term} ", True)

    def open_in_browser(self, url):
        webbrowser.open(url)

    def copy_to_clipboard(self, url):
        print(json.dumps({"method": "Flow.Launcher.CopyToClipboard","parameters":[url]}))

if __name__ == "__main__":
    TenorFlow()
