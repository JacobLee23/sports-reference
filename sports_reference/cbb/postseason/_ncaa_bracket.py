"""
"""

import re
import typing

import bs4
import numpy as np
import pandas as pd
import requests

from sports_reference._binary_tree import BinaryTree, Node


class Team:
    """
    """
    index = pd.Index(["seed", "name", "href", "points", "boxscore", "winner"])

    def __init__(self, container: typing.Optional[bs4.Tag] = None):
        self._container = container

    def __repr__(self) -> str:
        return f"{type(self).__name__}(seed={self.seed}, name={self.name}, points={self.points})"

    def __str__(self) -> str:
        return f"({self.seed}) {self.name} [{self.points}]"

    def __eq__(self, other: "Team") -> bool:
        return (self.seed, self.name) == (other.seed, other.name)

    def __ne__(self, other: "Team") -> bool:
        return (self.seed, self.name) != (other.seed, other.name)

    def __lt__(self, other: "Team") -> bool:
        return (self.seed, self.name) < (other.seed, other.name)

    def __le__(self, other: "Team") -> bool:
        return (self.seed, self.name) <= (other.seed, other.name)

    def __gt__(self, other: "Team") -> bool:
        return (self.seed, self.name) > (other.seed, other.name)

    def __ge__(self, other: "Team") -> bool:
        return (self.seed, self.name) >= (other.seed, other.name)

    def __hash__(self) -> int:
        return hash((self.seed, self.name))

    @classmethod
    def node(cls, team: "Team") -> Node:
        """
        :param team:
        :return:
        """
        return Node(team)

    @property
    def seed(self) -> typing.Optional[int]:
        """
        :return:
        """
        if self._container is None:
            return None
        return int(self._container.select_one("span").text)

    @property
    def name(self) -> typing.Optional[str]:
        """
        :return:
        """
        if self._container is None:
            return None
        return self._container.select_one("a:nth-of-type(1)").text

    @property
    def href(self) -> typing.Optional[str]:
        """
        :return:
        """
        if self._container is None:
            return None
        return self._container.select_one("a:nth-of-type(1)").attrs["href"]

    @property
    def points(self) -> typing.Optional[int]:
        """
        :return:
        """
        if self._container is None:
            return None
        try:
            return int(self._container.select_one("a:nth-of-type(2)").text)
        except AttributeError:
            return None

    @property
    def boxscore(self) -> typing.Optional[str]:
        """
        :return:
        """
        if self._container is None:
            return None
        try:
            return self._container.select_one("a:nth-of-type(2)").attrs["href"]
        except AttributeError:
            return None

    @property
    def winner(self) -> typing.Optional[bool]:
        """
        :return:
        """
        if self._container is None:
            return None
        try:
            return "winner" in self._container.attrs["class"]
        except KeyError:
            return False

    def series(self) -> pd.Series:
        """
        :return:
        """
        if self._container is None:
            return pd.Series([np.nan, "", "", np.nan, "", False], index=self.index)
        return pd.Series({k: getattr(self, k) for k in self.index})


class Game:
    """
    """
    def __init__(self, container: bs4.Tag):
        self._container = container

        elements = self._container.select("div")
        self._a = Team(elements[0]) if elements[0].select_one("span") is not None else Team()
        try:
            self._b = Team(elements[1]) if elements[1].select_one("span") is not None else Team()
        except IndexError:
            self._b = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}(teams={self.teams}, winner={self.winner.__repr__()})"

    def __hash__(self) -> int:
        return hash(frozenset(self.teams))

    @property
    def a(self) -> typing.Optional[Team]:
        """
        :return:
        """
        return self._a

    @property
    def b(self) -> typing.Optional[Team]:
        """
        :return:
        """
        return self._b

    @property
    def winner(self) -> typing.Optional[Team]:
        """
        :return:
        """
        try:
            if self.a.winner and not self.b.winner:
                return self.a
            if not self.a.winner and self.b.winner:
                return self.b
        except AttributeError:
            return None

    @property
    def location(self) -> typing.Tuple[str, str]:
        """
        :return:
        """
        return re.search(
            r"^at (.*), ([A-Z]{2})$", self._container.select_one("span:last-child > a").text
        ).groups()

    @property
    def boxscore(self) -> typing.Optional[str]:
        """
        :return:
        """
        try:
            return self._container.select_one("span:last-child > a").attrs["href"]
        except KeyError:
            return None

    @property
    def teams(self) -> typing.Tuple[Team, Team]:
        """
        :return:
        """
        return (self.a, self.b)

    @property
    def score(self) -> typing.Dict[Team, int]:
        """
        :return:
        """
        return {x: x.points for x in self.teams}

    def dataframe(self) -> pd.DataFrame:
        """
        :return:
        """
        return pd.DataFrame(
            x.series() for x in filter((lambda x: x is not None), self.teams)
        )


class Round:
    """
    """
    def __init__(self, container: bs4.Tag, nround: int):
        self._container = container
        self._nround = nround

        self._games = list(map(Game, self._container.select("div:has(> div)")))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(nround={self.nround}, ngames={self.ngames})"

    @property
    def nround(self) -> int:
        """
        :return:
        """
        return self._nround

    @property
    def games(self) -> typing.List[Game]:
        """
        :return:
        """
        return self._games

    @property
    def ngames(self) -> int:
        """
        :return:
        """
        return len(self.games)

    def teams(self) -> typing.List[Team]:
        """
        :return:
        """
        return [team for game in self.games for team in game.teams]

    def dataframe(self) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = pd.concat([x.dataframe() for x in self.games]).reset_index(drop=True)
        dataframe.insert(0, "game", dataframe.index // 2)
        dataframe.insert(0, "nround", self.nround)
        return dataframe


class Bracket:
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup, region: str):
        self._container = soup.select_one(f"#brackets > #{region} > #bracket")
        self._region = region

        self._rounds = {
            i: Round(e, i) for i, e in enumerate(self._container.select("div.round"), 1)
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(region={self.region}, nrounds={self.nrounds})"

    @property
    def region(self) -> str:
        """
        :return:
        """
        return self._region

    @property
    def rounds(self) -> typing.Dict[int, Round]:
        """
        :return:
        """
        return self._rounds

    @property
    def nrounds(self) -> int:
        """
        :return:
        """
        return len(self.rounds)

    def games(self) -> typing.Dict[int, typing.List[Game]]:
        """
        :return:
        """
        return {nround: list(round.games) for nround, round in self.rounds.items()}

    def teams(self) -> typing.Dict[int, typing.List[Team]]:
        """
        :return:
        """
        return {k: [t for x in v for t in x.teams] for k, v in self.games().items()}

    def dataframe(self) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = pd.concat(
            [x.dataframe() for x in self.rounds.values()]
        ).reset_index(drop=True)
        dataframe.insert(0, "region", self.region)
        return dataframe

    def binary_tree(self) -> BinaryTree:
        """
        :return:
        """
        tree = BinaryTree(self.nrounds - 1)
        teams = {k: [Team.node(x) for x in v] for k, v in self.teams().items()}

        for nlevel, nodes in tree.levels(tree.root).items():
            for i, node in enumerate(nodes):
                node.data = teams[self.nrounds - nlevel][i]

        return tree


class Tournament:
    """
    """
    _address: str

    def __init__(self, year: int):
        self._year = year

        self._response = requests.get(self.address, timeout=10000)
        self._soup = bs4.BeautifulSoup(self._response.text, features="lxml")

        self._regions = tuple(e.attrs["id"] for e in self._soup.select("#brackets > div"))
        self._brackets = {x: Bracket(self._soup, x) for x in self.regions}

    def __repr__(self) -> str:
        return f"{type(self).__name__}(year={self.year}, regions={self.regions})"

    def __getattr__(self, name: str) -> Bracket:
        if name not in self.regions:
            raise AttributeError(name)
        return self.brackets[name]

    @property
    def address(self) -> str:
        """
        :return:
        """
        return self._address.format(year=self.year)

    @property
    def year(self) -> int:
        """
        :return:
        """
        return self._year

    @property
    def regions(self) -> typing.Tuple[str]:
        """
        :return:
        """
        return self._regions

    @property
    def brackets(self) -> typing.Dict[str, Bracket]:
        """
        :return:
        """
        return self._brackets

    def dataframe(self) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = pd.concat(
            [x.dataframe() for x in self.brackets.values()]
        ).reset_index(drop=True)
        dataframe.insert(0, "year", self.year)
        return dataframe
