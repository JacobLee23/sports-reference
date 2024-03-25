"""
"""

import re
import typing

import bs4
import requests


class Team:
    """
    """
    def __init__(self, container: bs4.Tag):
        self._container = container

    def __repr__(self) -> str:
        attributes = ("seed", "name", "href", "points", "boxscore", "winner")
        arguments = ", ".join(f"{k}={getattr(self, k)}" for k in attributes)
        return f"{type(self).name}({arguments})"

    def __str__(self) -> str:
        return f"({self.seed}) {self.name} [{self.points}]"

    def __hash__(self) -> int:
        return hash((self.seed, self.name))

    @property
    def seed(self) -> int:
        """
        :return:
        """
        return int(self._container.select_one("span").text)

    @property
    def name(self) -> str:
        """
        :return:
        """
        return self._container.select_one("a:nth-of-type(1)").text

    @property
    def href(self) -> str:
        """
        :return:
        """
        return self._container.select_one("a:nth-of-type(1)").attrs["href"]

    @property
    def points(self) -> int:
        """
        :return:
        """
        return int(self._container.select_one("a:nth-of-type(2)").text)

    @property
    def boxscore(self) -> str:
        """
        :return:
        """
        return self._container.select_one("a:nth-of-type(2)").attrs["href"]

    @property
    def winner(self) -> bool:
        """
        :return:
        """
        return "winner" in self._container.attrs["class"]


class Game:
    """
    """
    def __init__(self, container: bs4.Tag):
        self._container = container

        self._a = Team(self._container.select_one("div:nth-child(1)"))
        self._b = Team(self._container.select_one("div:nth-child(2)"))

        if self.a.winner and not self.b.winner:
            self._winner = self.a

    def __repr__(self) -> str:
        return f"{type(self).__name__}(a={self.a}, b={self.b})"

    def __hash__(self) -> int:
        return hash(frozenset(self.teams))

    @property
    def a(self) -> Team:
        """
        :return:
        """
        return self._a

    @property
    def b(self) -> Team:
        """
        :return:
        """
        return self._b

    @property
    def winner(self) -> typing.Optional[Team]:
        """
        :return:
        """
        if self.a.winner and not self.b.winner:
            return self.a
        elif not self.a.winner and self.b.winner:
            return self.b

    @property
    def location(self) -> typing.Tuple[str, str]:
        """
        :return:
        """
        return re.search(
            r"^at (.*), ([A-Z]{2})$", self._container.select_one("span").text
        ).groups()

    @property
    def boxscore(self) -> str:
        """
        :return:
        """
        return self._container.select_one("span").attrs["href"]

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


class Round:
    """
    """
    def __init__(self, container: bs4.Tag, nround: int):
        self._container = container
        self._nround = nround

        self._games = list(map(Game, self._container.select("div")))

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
    def teams(self) -> typing.FrozenSet[Team]:
        """
        :return:
        """
        return frozenset(team for game in self.games for team in game.teams)


class Bracket:
    """
    """
    def __init__(self, soup: bs4.BeautifulSoup, region: str):
        self._container = soup.select_one("#brackets > #{region} > #bracket")
        self._region = region

        self._rounds = {
            i: Round(e, i) for i, e in enumerate(self._container.select("div.round"), 1)
        }

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
    def games(self) -> typing.FrozenSet[Game]:
        """
        :return:
        """
        return frozenset(game for round in self.rounds.values() for game in round.games)

    @property
    def teams(self) -> typing.FrozenSet[Team]:
        """
        :return:
        """
        return frozenset(team for game in self.games for team in game.teams)


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


class MensTournament(Tournament):
    """
    """
    _address = "https://www.sports-reference.com/cbb/postseason/men/{year}-ncaa.html"


class WomensTournament(Tournament):
    """
    """
    _address = "https://www.sports-reference.com/cbb/postseason/women/{year}-ncaa.html"
