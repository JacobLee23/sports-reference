"""
"""

import datetime
import io
import operator
import re
import string
import typing

import bs4
import requests
import pandas as pd

from . import (
    HEADERS, ROOT
)


class PlayerIndex:
    """
    """
    _address = f"{ROOT}/players/{{letter}}"

    def __init__(self, letter: str):
        if len(letter) != 1 or letter not in string.ascii_letters:
            raise ValueError(letter)
        self._letter = letter.lower()

        self._response = requests.get(self.address, headers=HEADERS)
        self._soup = bs4.BeautifulSoup(self._response.text, features="lxml")

    def __repr__(self) -> str:
        return f"{type(self).__name__}(letter={self.letter})"

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
    def standard_batting(self) -> typing.Optional["StandardBatting"]:
        """
        """
        return self._standard_batting

    @property
    def playervalue_batting(self) -> typing.Optional["PlayerValueBatting"]:
        """
        """
        return self._playervalue_batting

    @property
    def standard_pitching(self) -> typing.Optional["StandardPitching"]:
        """
        """
        return self._standard_pitching

    @property
    def playervalue_pitching(self) -> typing.Optional["PlayerValuePitching"]:
        """
        """
        return self._playervalue_pitching

    @property
    def standard_fielding(self) -> typing.Optional["StandardFielding"]:
        """
        """
        return self._standard_fielding


class _StatTable:
    """
    """
    _re_stats = re.compile(r"\d{4}")
    _re_totals = re.compile(r"^(\d+) (Yr|Season)s?$")
    _re_averages = re.compile(r"^162 Game Avg\.$")
    _re_teams = re.compile(r"^([A-Z]{3}) \((\d)+ yrs?\)$")
    _re_leagues = re.compile(r"^([A-Z]{2}) \((\d)+ yrs?\)$")

    def __init__(self, soup: bs4.BeautifulSoup, css_container: str, css_table: str):
        container = soup.select_one(css_container)
        if (table := container.select_one(css_table)) is None:
            table = container.find(string=lambda x: isinstance(x, bs4.Comment))

        with io.StringIO(str(table)) as buffer:
            dataframes = pd.read_html(buffer)

            if len(dataframes) != 1:
                raise ValueError

        self._dataframe = dataframes[0].dropna(how="all")

    @property
    def stats(self) -> pd.DataFrame:
        """
        """
        return self._stats()

    @property
    def totals(self) -> pd.Series:
        """
        """
        return self._totals()

    @property
    def averages(self) -> pd.Series:
        """
        """
        return self._averages()

    @property
    def teams(self) -> pd.DataFrame:
        """
        """
        return self._teams()

    @property
    def leagues(self) -> pd.DataFrame:
        """
        """
        return self._leagues()

    def _slice_dataframe(self, pattern: re.Pattern) -> pd.DataFrame:
        """
        """
        return self._dataframe.loc[
            self._dataframe.loc[:, "Year"].apply(lambda x: pattern.search(x) is not None), :
        ].reset_index(drop=True)

    def _stats(self) -> pd.DataFrame:
        """
        :return:
        """
        return self._slice_dataframe(self._re_stats)

    def _totals(self) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = self._slice_dataframe(self._re_totals)
        seasons = pd.Series(
            int(self._re_totals.search(x).group(1)) for x in dataframe.loc[:, "Year"]
        )
        dataframe.drop(columns=["Year", "Age", "Tm", "Lg"], inplace=True)
        dataframe.insert(1, "Seasons", seasons)

        return dataframe

    def _averages(self) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = self._slice_dataframe(self._re_averages)
        dataframe.drop(columns=["Year", "Age", "Tm", "Lg"], inplace=True)

        return dataframe

    def _teams(self) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = self._slice_dataframe(self._re_teams)
        seasons = pd.Series(
            int(self._re_teams.search(x).group(2)) for x in dataframe.loc[:, "Year"]
        )
        dataframe.loc[:, "Tm"] = dataframe.loc[:, "Year"].apply(
            lambda x: self._re_teams.search(x).group(1)
        )
        dataframe.drop(columns=["Year", "Age", "Lg"], inplace=True)
        dataframe.insert(1, "Seasons", seasons)

        return dataframe

    def _leagues(self) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = self._slice_dataframe(self._re_leagues)
        seasons = pd.Series(
            int(self._re_leagues.search(x).group(2)) for x in dataframe.loc[:, "Year"]
        )
        dataframe.loc[:, "Lg"] = dataframe.loc[:, "Year"].apply(
            lambda x: self._re_leagues.search(x).group(1)
        )
        dataframe.drop(columns=["Year", "Age", "Tm"], inplace=True)
        dataframe.insert(1, "Seasons", seasons)

        return dataframe


class _Standard(_StatTable):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup, css_container: str, css_table: str):
        super().__init__(soup, css_container, css_table)

    @property
    def totals(self) -> pd.Series:
        """
        """
        series = self._totals().iloc[0, :]
        series.name = None
        return series

    @property
    def averages(self) -> pd.Series:
        """
        """
        series = self._averages().iloc[0, :]
        series.name = None
        return series


class _PlayerValue(_StatTable):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup, css_container: str, css_table: str):
        super().__init__(soup, css_container, css_table)

    @property
    def totals(self) -> pd.Series:
        """
        """
        series = self._totals().iloc[0, :]
        series.name = None
        return series

    @property
    def averages(self) -> pd.Series:
        """
        """
        series = self._averages().iloc[0, :]
        series.name = None
        return series


class StandardBatting(_Standard):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup):
        super().__init__(soup, "div#all_batting_standard", "table#batting_standard")


class StandardPitching(_Standard):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup):
        super().__init__(soup, "div#all_pitching_standard", "table#pitching_standard")


class StandardFielding(_StatTable):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup):
        super().__init__(soup, "div#all_standard_fielding", "table#standard_fielding")

        self._dataframe = self._dataframe.loc[
            ~self._dataframe.loc[:, ["Year", "Age", "Tm"]].isna().all(axis=1), :
        ]

    @property
    def totals(self) -> pd.DataFrame:
        """
        """
        return self._totals()


class PlayerValueBatting(_PlayerValue):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup):
        super().__init__(soup, "div#all_batting_value", "table#batting_value")


class PlayerValuePitching(_PlayerValue):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup):
        super().__init__(soup, "div#all_pitching_value", "table#pitching_value")
