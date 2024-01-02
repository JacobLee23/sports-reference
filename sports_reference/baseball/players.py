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
        except AttributeError:
            self._standard_batting = None

        try:
            self._standard_pitching = StandardPitching(self._soup)
        except AttributeError:
            self._standard_pitching = None

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
    def standard_pitching(self) -> typing.Optional["StandardPitching"]:
        """
        """
        return self._standard_pitching


class _Standard:
    """
    """
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
        return self._dataframe.loc[
            self._dataframe.loc[:, "Year"].str.isdecimal(), :
        ].reset_index(drop=True)

    @property
    def career_totals(self) -> pd.Series:
        """
        """
        regex = re.compile(r"^(\d+) Yrs?$")

        dataframe = self._dataframe.loc[
            self._dataframe.loc[:, "Year"].apply(lambda x: regex.search(x) is not None)
        ].reset_index(drop=True)
        dataframe.insert(
            0, "Years", [int(regex.search(x).group(1)) for x in dataframe.loc[:, "Year"]]
        )
        dataframe.drop(columns=["Year", "Age", "Tm", "Lg"], inplace=True)

        series = pd.Series(dataframe.iloc[0, :])
        series.name = None

        return series

    @property
    def career_averages(self) -> pd.Series:
        """
        """
        dataframe = self._dataframe.loc[self._dataframe.loc[:, "Year"] == "162 Game Avg."].drop(
            columns=["Year", "Age", "Tm", "Lg"]
        ).reset_index(drop=True)

        series = pd.Series(dataframe.iloc[0, :])
        series.name = None

        return series

    @property
    def team_summaries(self) -> pd.DataFrame:
        """
        """
        regex = re.compile(r"^([A-Z]{3}) \((\d)+ yrs?\)$")

        dataframe = self._dataframe.loc[
            self._dataframe.loc[:, "Year"].apply(lambda x: regex.search(x) is not None)
        ].reset_index(drop=True)
        dataframe.insert(
            0, "Years", [int(regex.search(x).group(2)) for x in dataframe.loc[:, "Year"]]
        )
        dataframe.loc[:, "Tm"] = dataframe.loc[:, "Year"].apply(
            lambda x: regex.search(x).group(1)
        )
        dataframe.drop(columns=["Year", "Age", "Lg"], inplace=True)

        return dataframe

    @property
    def league_summaries(self) -> pd.DataFrame:
        """
        """
        regex = re.compile(r"^([A-Z]{2}) \((\d+) yrs?\)$")

        dataframe = self._dataframe.loc[
            self._dataframe.loc[:, "Year"].apply(lambda x: regex.search(x) is not None)
        ].reset_index(drop=True)
        dataframe.insert(
            0, "Years", [int(regex.search(x).group(2)) for x in dataframe.loc[:, "Year"]]
        )
        dataframe.loc[:, "Lg"] = dataframe.loc[:, "Year"].apply(
            lambda x: regex.search(x).group(1)
        )
        dataframe.drop(columns=["Year", "Age", "Tm"], inplace=True)

        return dataframe


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
