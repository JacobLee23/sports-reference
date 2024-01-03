"""
"""

import io
import re

import bs4
import pandas as pd


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
        dataframe.insert(1, "Seasons", seasons)

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


class _Standard(_StatTable):
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup, css_container: str, css_table: str):
        super().__init__(soup, css_container, css_table)

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
    def __init__(self, soup: bs4.BeautifulSoup, css_container: str, css_table: str):
        super().__init__(soup, css_container, css_table)
    
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
