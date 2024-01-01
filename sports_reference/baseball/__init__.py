"""
"""

import json
import pathlib


ROOT = "https://baseball-reference.com/"

with open(
    pathlib.Path(__file__).parent.parent / "data" / "headers.json", "r", encoding="utf-8"
) as file:
    HEADERS = json.load(file)
