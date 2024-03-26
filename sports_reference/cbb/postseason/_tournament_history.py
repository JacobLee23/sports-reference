"""
"""

import bs4
import pandas as pd
import requests


class NCAATournamentHistory:
    """
    """
    _address = "https://www.sports-reference.com/cbb/postseason/"

    def __init__(self):
        self._response = requests.get(self.address, timeout=10000)
        self._soup = bs4.BeautifulSoup(self._response.text, features="lxml")

    @property
    def address(self) -> str:
        """
        :return:
        """
        return self._address

    @property
    def mens(self) -> pd.DataFrame:
        """
        :return:
        """
        return pd.read_html(
            str(self._soup.select_one("table#ncaa-tournament-history_NCAAM"))
        )[0]

    @property
    def womens(self) -> pd.DataFrame:
        """
        :return:
        """
        return pd.read_html(
            str(self._soup.select_one("table#ncaa-tournament-history_NCAAW"))
        )[0]
