"""
"""

import string


class PlayerIndex:
    """
    """
    _address = "https://www.baseball-reference.com/players/{letter}/"

    def __init__(self, letter: str):
        if len(letter) != 1 or letter not in string.ascii_letters:
            raise ValueError(letter)
        self._letter = letter.lower()

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
