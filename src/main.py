"""Main file."""

import re

from .control import Control
from .puzzle.board import Board
from .puzzle.puzzles import puzzles
from .puzzle.board_tools import BoardTools


def main():
    """Main function."""

    pz = puzzles[5]
    rows = pz["rows"]
    cols = pz["cols"]
    data = re.sub(r"\s+", "", pz["data"])

    BoardTools.rows = rows
    BoardTools.cols = cols
    board = Board.fromString(rows, cols, data)

    control = Control(board)
    control.start()
