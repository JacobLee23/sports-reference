"""
"""

import datetime
import re
import typing

import bs4
import pandas as pd
import requests


class Player:
    """
    """
    _address = "https://www.baseball-reference.com/players/{letter}/{id}.shtml"

    _positions = [
        "Designated Hitter", "Pitcher", "Catcher", "First Baseman", "Second Baseman",
        "Third Baseman", "Shortstop", "Leftfielder", "Centerfielder", "Rightfielder"
    ]

    def __init__(self, id: str):
        self._id = id

        self._response = requests.get(self.address)
        self._soup = bs4.BeautifulSoup(self._response.text, features="lxml")

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}, name={self.name})"

    @property
    def id(self) -> str:
        """
        """
        return self._id
    
    @property
    def address(self) -> str:
        """
        """
        return self._address.format(letter=self.id[0], id=self.id)
    
    @property
    def meta(self) -> pd.Series:
        """
        """
        return pd.Series(
            {
                "Name": self.name,
                "Positions": self.positions,
                "Bats": self.bats,
                "Throws": self.throws,
                "HeightImperial": self.height[0],
                "HeightSI": self.height[1],
                "WeightImperial": self.weight[0],
                "WeightSI": self.weight[1],
                "Birthdate": self.birthdate,
                "Country": self.country
            }
        )

    @property
    def name(self) -> str:
        """
        """
        return self._soup.select_one("div#meta > div > h1:first-child").text.strip()

    @property
    def positions(self) -> str:
        """
        """
        return "".join(
            str(i) for i, x in enumerate(self._positions) if x in self._soup.select_one(
                "div#meta > div"
            ).text
        )

    @property
    def bats(self) -> str:
        """
        """
        return re.search(
            r"Bats:\s(Right|Left|Both)",
            self._soup.select_one("div#meta > div").text.strip()
        ).group(1)

    @property
    def throws(self) -> str:
        """
        """
        return re.search(
            r"Throws:\s(Right|Left|Both)",
            self._soup.select_one("div#meta > div").text.strip()
        ).group(1)

    @property
    def height(self) -> typing.Tuple[int, int]:
        """
        """
        foot, inch, _, centimeter, _ = map(
            int, re.search(
                r"(\d+)-(\d+),\s(\d+)lb\s\((\d+)cm,\s(\d+)kg\)",
                self._soup.select_one("div#meta > div").text.strip()
            ).groups()
        )
        return 12 * foot + inch, centimeter

    @property
    def weight(self) -> typing.Tuple[int, int]:
        """
        """
        _, _, pound, _, kilogram = map(
            int, re.search(
                r"(\d+)-(\d+),\s(\d+)lb\s\((\d+)cm,\s(\d+)kg\)",
                self._soup.select_one("div#meta > div").text.strip()
            ).groups()
        )
        return pound, kilogram

    @property
    def birthdate(self) -> datetime.datetime:
        """
        """
        return datetime.datetime.strptime(
            self._soup.select_one("span#necro-birth").attrs["data-birth"], "%Y-%m-%d"
        )

    @property
    def country(self) -> str:
        """
        """
        return self._soup.select_one(
            "div#meta > div > p:nth-of-type(4) > span.f-i"
        ).text.strip().upper()
