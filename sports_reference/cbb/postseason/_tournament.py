"""
"""

from ._ncaa_bracket import Tournament


class MensTournament(Tournament):
    """
    """
    _address = "https://www.sports-reference.com/cbb/postseason/men/{year}-ncaa.html"


class WomensTournament(Tournament):
    """
    """
    _address = "https://www.sports-reference.com/cbb/postseason/women/{year}-ncaa.html"
