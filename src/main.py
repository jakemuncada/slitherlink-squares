"""Main file."""

import re

from .control import Control
from .puzzle.board import Board
from .puzzle.puzzles import puzzles


def main():
    """Main function."""

    pz = puzzles[3]
    rows = pz["rows"]
    cols = pz["cols"]
    data = re.sub(r"\s+", "", pz["data"])

    board = Board.fromString(rows, cols, data)

    control = Control(board)
    control.start()
