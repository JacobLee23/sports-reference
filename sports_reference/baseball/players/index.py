"""
"""

import re
import string

import bs4
import pandas as pd
import requests

from sports_reference.baseball import (
    HEADERS, ROOT
)


def player_index(letter: str) -> pd.DataFrame:
    """
    :param letter:
    :return:
    :raise ValueError:
    """
    if len(letter) != 1 or letter not in string.ascii_letters:
        raise ValueError(letter)
    
    with requests.get(f"{ROOT}/players/{letter.lower()}", headers=HEADERS) as response:
        soup = bs4.BeautifulSoup(response.text, features="lxml")

    container = soup.select_one("#div_players_")
    
    re_href = re.compile(r"^/players/[a-z]/(\w+)\.shtml$")
    re_text = re.compile(r"\((\d+)-(\d+)\)")

    dataframe = pd.DataFrame(columns=["ID", "Name", "URL", "YearStart", "YearEnd", "Active", "HoF"])
    for idx, element in enumerate(container.select("p")):
        href = element.select_one("a").attrs["href"]
        dataframe.loc[idx, :] = {
            "ID": re_href.search(href).group(1),
            "Name": element.select_one("a").text,
            "URL": href,
            "YearStart": int(re_text.search(element.text).group(1)),
            "YearEnd": int(re_text.search(element.text).group(2)),
            "Active": element.select_one("b") is not None,
            "Hof": "+" in element.text
        }

    return dataframe
