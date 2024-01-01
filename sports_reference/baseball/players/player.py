"""
"""

import bs4
import requests


class Player:
    """
    """
    _address = "https://www.baseball-reference.com/players/{letter}/{id}.shtml"

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
    def name(self) -> str:
        """
        """
        return self._soup.select_one("div#meta > div > h1 > span").text
