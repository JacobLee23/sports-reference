"""
"""

import io
import re

import bs4
import numpy as np
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
        table = self._soup.select_one("table#ncaa-tournament-history_NCAAM")
        dataframe = self._dataframe(table)

        data_stats = {"NIT Champion": "nit_champ", "NIT MVP": "nit_mvp_winner"}
        for label, css in data_stats.items():
            columns = dataframe.columns.to_list()
            dataframe.insert(
                columns.index(label) + 1, f"{label} [href]", self._data_stat(table, css)
            )

        return dataframe

    @property
    def womens(self) -> pd.DataFrame:
        """
        :return:
        """
        table = self._soup.select_one("table#ncaa-tournament-history_NCAAW")
        return self._dataframe(table)

    def _dataframe(self, table: bs4.Tag) -> pd.DataFrame:
        """
        :param table:
        :return:
        :raise ValueError:
        """
        with io.StringIO(str(table)) as buffer:
            dataframe = pd.read_html(buffer)[0]

        dataframe.insert(
            0, "Year", pd.Series(
                dataframe.loc[:, "NCAA Tournament"].apply(
                    lambda x: int(
                        re.search(r"^(\d{4}) NCAA$", x).group(1)
                    ) if isinstance(x, str) else np.nan
                ), dtype="Int64"
            )
        )

        data_stats = {
            "NCAA Tournament": "ncaa_tourney",
            "NCAA Champion": "ncaa_champ",
            "NCAA MOP": "ncaa_mop_winner"
        }
        for label, css in data_stats.items():
            columns = dataframe.columns.to_list()
            dataframe.insert(
                columns.index(label) + 1, f"{label} [href]", self._data_stat(table, css)
            )

        return dataframe

    def _data_stat(self, table: bs4.Tag, css: str) -> pd.Series:
        """
        :param table:
        :param css:
        :return:
        """
        return pd.Series(
            [
                "" if e.select_one("a") is None else e.select_one("a").attrs["href"]
                for e in table.select(f"tr.valign_top > *[data-stat='{css}']")
            ]
        )
