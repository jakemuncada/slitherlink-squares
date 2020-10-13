"""Main file."""

import re
from board import Board
from puzzles import puzzles


def main():
    """Main function."""

    rows = puzzles[0]["rows"]
    cols = puzzles[0]["cols"]
    data = re.sub(r"\s+", "", puzzles[0]["data"])

    board = Board.fromString(rows, cols, data)


if __name__ == "__main__":
    main()
