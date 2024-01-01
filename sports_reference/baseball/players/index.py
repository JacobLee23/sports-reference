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

    def __repr__(self) -> str:
        return f"{type(self).__name__}(letter={self.letter})"
    
    def __getitem__(self, item: str) -> pd.Series:
        """
        """
        return self.dataframe.loc[:, item]

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
            dataframe.loc[i, :] = {
                "ID": regex_href.search(href).group(1),
                "Name": element.select_one("a").text,
                "URL": href,
                "YearStart": int(regex_text.search(element.text).group(1)),
                "YearEnd": int(regex_text.search(element.text).group(2)),
                "Active": element.select_one("b") is not None,
                "Hof": "+" in element.text
            }

        return dataframe
