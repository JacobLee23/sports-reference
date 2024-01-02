"""
"""

import datetime
import operator
import re
import typing

import bs4
import pandas as pd
import requests

from ._overview import (
    StandardBatting, StandardPitching, StandardFielding,
    PlayerValueBatting, PlayerValuePitching
)
from sports_reference.baseball import (
    HEADERS, ROOT
)


class Player:
    """
    """
    _address = f"{ROOT}/players/{{letter}}/{{id}}.shtml"

    _positions = [
        "Designated Hitter", "Pitcher", "Catcher", "First Baseman", "Second Baseman",
        "Third Baseman", "Shortstop", "Leftfielder", "Centerfielder", "Rightfielder"
    ]

    def __init__(self, id: str):
        self._id = id

        self._response = requests.get(self.address, headers=HEADERS)
        if self._response.status_code == 404:
            raise ValueError(self.id)
        self._soup = bs4.BeautifulSoup(self._response.text, features="lxml")

        try:
            self._standard_batting = StandardBatting(self._soup)
            self._playervalue_batting = PlayerValueBatting(self._soup)
        except AttributeError:
            self._standard_batting = None
            self._playervalue_batting = None

        try:
            self._standard_pitching = StandardPitching(self._soup)
            self._playervalue_pitching = PlayerValuePitching(self._soup)
        except AttributeError:
            self._standard_pitching = None
            self._playervalue_pitching = None

        try:
            self._standard_fielding = StandardFielding(self._soup)
        except AttributeError:
            self._standard_fielding = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}, address={self.address}, meta={self.meta})"

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
        element_meta = self._soup.select_one("div#meta > div:nth-child(2)")
        text_meta = element_meta.text.strip()

        regex_bats = re.compile(r"Bats:\s(Right|Left|Both)")
        regex_throws = re.compile(r"Throws:\s(Right|Left|Both)")
        regex_height = re.compile(r"(\d+)-(\d+),\s\d+lb\s\((\d+)cm,\s\d+kg\)")
        regex_weight = re.compile(r"\d+-\d+,\s(\d+)lb\s\(\d+cm,\s(\d+)kg\)")

        return pd.Series(
            {
                "Name": element_meta.select_one("h1:first-child").text.strip(),
                "Positions": "".join(
                    str(i) for i, x in enumerate(self._positions)
                    if x in text_meta
                ),
                "Bats": regex_bats.search(text_meta).group(1),
                "Throws": regex_throws.search(text_meta).group(1),
                "HeightImperial": operator.mul(
                    int(regex_height.search(text_meta).group(1)),
                    int(regex_height.search(text_meta).group(2))
                ),
                "HeightSI": int(regex_height.search(text_meta).group(3)),
                "WeightImperial": int(regex_weight.search(text_meta).group(1)),
                "WeightSI": int(regex_weight.search(text_meta).group(2)),
                "Birthdate": datetime.datetime.strptime(
                    element_meta.select_one("span#necro-birth").attrs["data-birth"], "%Y-%m-%d"
                ),
                "Country": element_meta.select_one(
                    "p:nth-of-type(4) > span.f-i"
                ).text.strip().upper()
            }
        )
    
    @property
    def standard_batting(self) -> typing.Optional[StandardBatting]:
        """
        """
        return self._standard_batting

    @property
    def playervalue_batting(self) -> typing.Optional[PlayerValueBatting]:
        """
        """
        return self._playervalue_batting

    @property
    def standard_pitching(self) -> typing.Optional[StandardPitching]:
        """
        """
        return self._standard_pitching

    @property
    def playervalue_pitching(self) -> typing.Optional[PlayerValuePitching]:
        """
        """
        return self._playervalue_pitching

    @property
    def standard_fielding(self) -> typing.Optional[StandardFielding]:
        """
        """
        return self._standard_fielding
