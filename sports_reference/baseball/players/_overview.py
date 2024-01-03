"""
"""

import io
import re
import typing

import bs4
import numpy as np
import pandas as pd


class Overview:
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup):
        self._soup = soup

        try:
            self._standard_batting = StandardBatting(soup)
            self._playervalue_batting = PlayerValueBatting(soup)
            self._advanced_batting = AdvancedBatting(soup)
        except AttributeError:
            self._standard_batting = None
            self._playervalue_batting = None
            self._advanced_batting = None

        try:
            self._standard_pitching = StandardPitching(soup)
            self._playervalue_pitching = PlayerValueBatting(soup)
            self._advanced_pitching = AdvancedPitching(soup)
        except AttributeError:
            self._standard_pitching = None
            self._playervalue_pitching = None
            self._advanced_pitching = None

        try:
            self._standard_fielding = StandardFielding(soup)
        except AttributeError:
            self._standard_fielding = None

        try:
            self._projections = Projections(soup)
        except AttributeError:
            self._projections = None

    @property
    def soup(self) -> bs4.BeautifulSoup:
        """
        """
        return self._soup

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
    def advanced_batting(self) -> typing.Optional["AdvancedBatting"]:
        """
        """
        return self._advanced_batting
    
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
    def advanced_pitching(self) -> typing.Optional["AdvancedPitching"]:
        """
        """
        return self._advanced_pitching
    
    @property
    def standard_fielding(self) -> typing.Optional["StandardFielding"]:
        """
        """
        return self._standard_fielding
    
    @property
    def projections(self) -> typing.Optional["Projections"]:
        """
        """
        return self._projections


class _StatTable:
    """
    """
    _re_stats = re.compile(r"\d{4}")
    _re_totals = re.compile(r"^(\d+) (Yr|Season)s?$")
    _re_averages = re.compile(r"^162 Game Avg\.$")
    _re_teams = re.compile(r"^([A-Z]{3}) \((\d)+ yrs?\)$")
    _re_leagues = re.compile(r"^([A-Z]{2}) \((\d)+ yrs?\)$")

    def __init__(self, soup: bs4.BeautifulSoup, css_container: str, css_table: str):
        self._soup = soup
        self._dataframe = self._scrape_table(self.soup, css_container, css_table).dropna(how="all")

    @classmethod
    def _scrape_table(
        cls, soup: bs4.BeautifulSoup, css_container: str, css_table: str
    ) -> pd.DataFrame:
        """
        :param soup:
        :param css_container:
        :param css_table:
        :return:
        """
        container = soup.select_one(css_container)
        if (table := container.select_one(css_table)) is None:
            table = container.find(string=lambda x: isinstance(x, bs4.Comment))

        with io.StringIO(str(table)) as buffer:
            dataframes = pd.read_html(buffer)
            
        return dataframes[0]

    @classmethod
    def _stats(cls, dataframe: pd.DataFrame, pattern: re.Pattern = _re_stats) -> pd.DataFrame:
        """
        :return:
        """
        return dataframe.loc[
            dataframe.loc[:, "Year"].apply(lambda x: pattern.search(x) is not None), :
        ].reset_index(drop=True)

    @classmethod
    def _totals(cls, dataframe: pd.DataFrame, pattern: re.Pattern = _re_totals) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = dataframe.loc[
            dataframe.loc[:, "Year"].apply(lambda x: pattern.search(x) is not None), :
        ].reset_index(drop=True)
        seasons = pd.Series(
            int(pattern.search(x).group(1)) for x in dataframe.loc[:, "Year"]
        )
        dataframe.drop(columns=["Year", "Age", "Tm", "Lg"], inplace=True)
        dataframe.insert(0, "Seasons", seasons)

        return dataframe

    @classmethod
    def _averages(cls, dataframe: pd.DataFrame, pattern: re.Pattern = _re_averages) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = dataframe.loc[
            dataframe.loc[:, "Year"].apply(lambda x: pattern.search(x) is not None), :
        ].reset_index(drop=True)
        dataframe.drop(columns=["Year", "Age", "Tm", "Lg"], inplace=True)

        return dataframe

    @classmethod
    def _teams(cls, dataframe: pd.DataFrame, pattern: re.Pattern = _re_teams) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = dataframe.loc[
            dataframe.loc[:, "Year"].apply(lambda x: pattern.search(x) is not None), :
        ].reset_index(drop=True)
        seasons = pd.Series(
            int(pattern.search(x).group(2)) for x in dataframe.loc[:, "Year"]
        )
        dataframe.loc[:, "Tm"] = dataframe.loc[:, "Year"].apply(
            lambda x: pattern.search(x).group(1)
        )
        dataframe.drop(columns=["Year", "Age", "Lg"], inplace=True)
        dataframe.insert(1, "Seasons", seasons)

        return dataframe

    @classmethod
    def _leagues(cls, dataframe: pd.DataFrame, pattern: re.Pattern = _re_leagues) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = dataframe.loc[
            dataframe.loc[:, "Year"].apply(lambda x: pattern.search(x) is not None)
        ].reset_index(drop=True)
        seasons = pd.Series(
            int(pattern.search(x).group(2)) for x in dataframe.loc[:, "Year"]
        )
        dataframe.loc[:, "Lg"] = dataframe.loc[:, "Year"].apply(
            lambda x: pattern.search(x).group(1)
        )
        dataframe.drop(columns=["Year", "Age", "Tm"], inplace=True)
        dataframe.insert(1, "Seasons", seasons)

        return dataframe
    
    @property
    def soup(self) -> bs4.BeautifulSoup:
        """
        """
        return self._soup


class _Standard(_StatTable):
    """
    """
    @property
    def stats(self) -> pd.DataFrame:
        """
        """
        return self._stats(self._dataframe)

    @property
    def totals(self) -> pd.Series:
        """
        """
        series = self._totals(self._dataframe).iloc[0, :]
        series.name = None
        return series

    @property
    def averages(self) -> pd.Series:
        """
        """
        series = self._averages(self._dataframe).iloc[0, :]
        series.name = None
        return series

    @property
    def teams(self) -> pd.DataFrame:
        """
        """
        return self._teams(self._dataframe)

    @property
    def leagues(self) -> pd.DataFrame:
        """
        """
        return self._leagues(self._dataframe)


class _PlayerValue(_StatTable):
    """
    """
    @property
    def stats(self) -> pd.DataFrame:
        """
        """
        return self._stats(self._dataframe)

    @property
    def totals(self) -> pd.Series:
        """
        """
        series = self._totals(self._dataframe).iloc[0, :]
        series.name = None
        return series

    @property
    def averages(self) -> pd.Series:
        """
        """
        series = self._averages(self._dataframe).iloc[0, :]
        series.name = None
        return series

    @property
    def teams(self) -> pd.DataFrame:
        """
        """
        return self._teams(self._dataframe)

    @property
    def leagues(self) -> pd.DataFrame:
        """
        """
        return self._leagues(self._dataframe)
    

class _Advanced(_StatTable):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup, css_container: str, css_table: str):
        super().__init__(soup, css_container, css_table)

        self._columns = pd.MultiIndex.from_tuples(
            ("Meta", x[1]) if "Unnamed" in x[0] else x for x in self._dataframe.columns
        )
        self._dataframe.columns = self._columns
    
    @property
    def stats(self) -> pd.DataFrame:
        """
        """
        dataframe = self._stats(self._dataframe.droplevel(0, axis=1))
        dataframe.columns = self._dataframe.columns
        return dataframe
    
    @property
    def totals(self) -> pd.Series:
        """
        """
        colmap = {x[1]: x[0] for x in self._columns}
        series = self._totals(self._dataframe.droplevel(0, axis=1)).iloc[0, :]
        series.index = pd.MultiIndex.from_tuples(
            (colmap.get(x, "Meta"), x) for x in series.index
        )
        series.name = None
        return series
    
    @property
    def averages(self) -> pd.Series:
        """
        """
        colmap = {x[1]: x[0] for x in self._columns}
        series = self._averages(
            self._dataframe.droplevel(0, axis=1), re.compile(r"^MLB Averages$")
        ).iloc[0, :]
        series.index = pd.MultiIndex.from_tuples(
            (colmap.get(x, "Meta"), x) for x in series.index
        )
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
    def stats(self) -> pd.DataFrame:
        """
        """
        return self._stats(self._dataframe)

    @property
    def totals(self) -> pd.Series:
        """
        """
        return self._totals(self._dataframe)


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


class AdvancedBatting(_Advanced):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup):
        super().__init__(soup, "div#all_batting_advanced", "table#batting_advanced")


class AdvancedPitching(_Advanced):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup):
        super().__init__(soup, "div#all_pitching_advanced", "table#pitching_advanced")


class Projections(_StatTable):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup):
        try:
            super().__init__(soup, "div#all_batting_proj", "table#batting_proj")
        except AttributeError:
            super().__init__(soup, "div#all_pitching_proj", "table#pitching_proj")

        self._dataframe.columns = [
            "".join(filter(lambda c: isinstance(c, str), x)) for x in self._dataframe.columns
        ]

    @property
    def stats(self) -> pd.Series:
        """
        """
        series = self._dataframe.iloc[0, :]
        series.name = None
        return series
