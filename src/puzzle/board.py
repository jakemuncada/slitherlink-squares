"""Board"""

from copy import deepcopy
from functools import cache
from typing import Optional
from .enums import BorderStatus, CardinalDirection, Coord, OptInt


class Board:
    """The game board."""

    rows: int = 0
    """The number of rows of the board."""

    cols: int = 0
    """The number of columns of the board."""

    cells: list[list[OptInt]] = [[]]
    """The two-dimensional array containing the required sides of each cell."""

    borders: list[BorderStatus] = []
    """The array containing the status of each border."""

    def __init__(self, rows: int, cols: int, cells: Optional[list[list[OptInt]]] = None,
        borders: Optional[list[BorderStatus]] = None):
        """
        Creates a game board.

        Args:
            rows: The number of rows of the board. Must be a positive number.
            rows:  The number of columns of the board. Must be a positive number.
            cells: A two-dimensional array containing the required sides of each cell.
            borders: A two-dimensional array containing the status of each border.
        """
        if rows <= 0 or cols <= 0:
            raise ValueError("Row or column must be a positive number.")

        if cells is not None and (len(cells) != rows or len(cells[0]) != cols):
            raise ValueError("The given cell data does not match " \
                             "the number of rows and columns of the board.")

        if borders is not None and (len(borders) != rows + 1 or len(borders[0]) != cols + 1):
            raise ValueError("The given border data has invalid number of rows and columns.")

        self.rows = rows
        self.cols = cols
        self.cells = cells if cells is not None else \
            [[None for _ in range(cols)] for _ in range(rows)]
        self.borders = borders if borders is not None else \
            [BorderStatus.UNSET for _ in range((((cols * 2) + 1) * rows) + cols)]

    @classmethod
    def fromString(cls, rows: int, cols: int, cellDataString: str):
        """
        Creates a game board given the cells data as a string.

        Args:
            rows (int): The number of rows of the board. Must be a positive number.
            rows (int): The number of columns of the board. Must be a positive number.
            cellDataString (string): A string containing the required sides of each cell.
        """
        if rows <= 0 or cols <= 0:
            raise ValueError("Row or column must be a positive number.")

        if len(cellDataString) != rows * cols:
            raise ValueError("The given cell data does not match " +
                             "the number of rows and columns of the board.")

        idx: int = 0
        cells: list[list[OptInt]] = []
        for _ in range(rows):
            rowArr: list[OptInt] = []
            for _ in range(cols):
                val: OptInt = int(cellDataString[idx]) if cellDataString[idx] != "." else None
                rowArr.append(val)
                idx += 1
            cells.append(rowArr)

        return cls(rows, cols, cells)

    def copy(self):
        """Returns a deep copy of the Board."""
        cellsCopy = deepcopy(self.cells)
        bordersCopy = deepcopy(self.borders)
        return Board(self.rows, self.cols, cellsCopy, bordersCopy)

    ##################################################
    # GET BORDERS
    ##################################################

    def getBorderStatus(self, row: int, col: int, direction: CardinalDirection) -> BorderStatus:
        """
        Get the status of the border of the specified cell.

        Arguments:
            row: The cell's row index.
            col: The cell's column index.
            direction: The direction of the target border.

        Returns:
            The border status of the target border.
        """
        idx = self.getBorderIdx(row, col, direction)
        return self.borders[idx]

    @cache
    def getBorderIdx(self, row: int, col: int, direction: CardinalDirection) -> int:
        """
        Get the index of the target border.

        Arguments:
            row: The cell's row index.
            col: The cell's column index.
            direction: The direction of the target border.

        Returns:
            The index of the target border.
        """
        idx = ((self.cols * 2) + 1) * row
        if direction == CardinalDirection.TOP:
            idx += col
        elif direction == CardinalDirection.LEFT:
            idx += self.cols + col
        elif direction == CardinalDirection.RIGHT:
            idx += self.cols + col + 1
        elif direction == CardinalDirection.BOT:
            idx += (self.cols * 2) + 1 + col
        else:
            raise IndexError()
        return idx

    def getUnsetBorders(self) -> list[Coord]:
        """Returns the list of all `UNSET` borders. Each border is defined by a (row, col) tuple."""
        unsetBorders: list[Coord] = []
        for i in range(len(self.borders)):
            for j in range(len(self.borders[i])):
                if self.borders[i][j] == BorderStatus.UNSET:
                    unsetBorders.append((i, j))
        return unsetBorders

    def getBordersOfCell(self, cellRow, cellCol):
        """Returns the list of borders of a given cell. Each border is defined by a (row, col) tuple."""
