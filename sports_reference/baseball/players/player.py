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
