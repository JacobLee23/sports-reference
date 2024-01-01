"""
"""

import re
import string

import bs4
import requests
import pandas as pd


class PlayerIndex:
    """
    """
    _address = "https://www.baseball-reference.com/players/{letter}/"

    def __init__(self, letter: str):
        if len(letter) != 1 or letter not in string.ascii_letters:
            raise ValueError(letter)
        self._letter = letter.lower()

        self._response = requests.get(self.address)
        self._soup = bs4.BeautifulSoup(self._response.text, features="lxml")

        self._dataframe = self._scrape()

    @property
    def letter(self) -> str:
        """
        """
        return self._letter

    @property
    def address(self) -> str:
        """
        """
        return self._address.format(letter=self.letter)
    
    @property
    def dataframe(self) -> pd.DataFrame:
        """
        """
        return self._dataframe
    
    def _scrape(self) -> pd.DataFrame:
        """
        """
        container = self._soup.select_one("#div_players_")

        regex_href = re.compile(r"^/players/[a-z]/(\w+)\.shtml$")
        regex_text = re.compile(r"\((\d+)-(\d+)\)")

        dataframe = pd.DataFrame(columns=["ID", "Name", "URL", "YearStart", "YearEnd", "Active", "HoF"])
        for i, element in enumerate(container.select("p")):
            href = element.select_one("a").attrs["href"]
            dataframe.loc[i, :] = [
                regex_href.search(href).group(1),
                element.select_one("a").text,
                href,
                int(regex_text.search(element.text).group(1)),
                int(regex_text.search(element.text).group(2)),
                "+" in element.text,
                element.select_one("b") is not None
            ]

        return dataframe
