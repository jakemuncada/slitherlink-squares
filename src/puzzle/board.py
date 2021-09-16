"""Board"""

from copy import deepcopy
from typing import Optional

from src.puzzle.board_tools import BoardTools
from src.puzzle.enums import BorderStatus, CardinalDirection, DiagonalDirection, OptInt


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
        self.tools = BoardTools(rows, cols)
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

    def clone(self):
        """
        Returns a deep copy of the Board.
        """
        cellsCopy = deepcopy(self.cells)
        bordersCopy = deepcopy(self.borders)
        return Board(self.rows, self.cols, cellsCopy, bordersCopy)

    ##################################################
    # BORDER STATUS SETTERS
    ##################################################

    def toggleBorder(self, borderIdx) -> None:
        """
        Toggle the target border's status.
        """
        if self.borders[borderIdx] == BorderStatus.UNSET:
            self.setBorderToActive(borderIdx)
        elif self.borders[borderIdx] == BorderStatus.ACTIVE:
            self.setBorderToBlank(borderIdx)
        elif self.borders[borderIdx] == BorderStatus.BLANK:
            self.setBorderToUnset(borderIdx)

    def setBorderStatus(self, borderIdx: int, newStatus: BorderStatus) -> None:
        """
        Set the target border to a new status.
        """
        self.borders[borderIdx] = newStatus

    def setBorderToUnset(self, borderIdx: int) -> None:
        """
        Set the target border's status to `UNSET`.
        """
        self.borders[borderIdx] = BorderStatus.UNSET

    def setBorderToActive(self, borderIdx: int) -> None:
        """
        Set the target border's status to `ACTIVE`.
        """
        self.borders[borderIdx] = BorderStatus.ACTIVE

    def setBorderToBlank(self, borderIdx: int) -> None:
        """
        Set the target border's status to `BLANK`.
        """
        self.borders[borderIdx] = BorderStatus.BLANK

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
        idx = self.tools.getBorderIdx(row, col, direction)
        return self.borders[idx]

    def getCornerBordersStatus(self, row: int, col: int, dxn: DiagonalDirection) -> tuple[BorderStatus, BorderStatus]:
        """
        Get the statuses of the two borders connected to the specified corner direction.

        Arguments:
            row: The cell's row index.
            col: The cell's column index.
            dxn: The direction of the target corner.

        Returns:
            the statuses of the two borders connected to the specified corner direction.
        """
        bdr1, bdr2 = self.tools.getCornerBorderIndices(row, col, dxn)
        stat1 = self.borders[bdr1]
        stat2 = self.borders[bdr2]
        return (stat1, stat2)

    def getUnsetBordersOfCell(self, row: int, col: int) -> list[int]:
        """
        Returns a list of the indices of the `UNSET` borders that surround a target cell.

        Arguments:
            row: The row index of the target cell.
            col: The column index of the target cell.
        """
        unsetBorders: list[int] = []
        for direction in CardinalDirection:
            idx = self.tools.getBorderIdx(row, col, direction)
            if self.borders[idx] == BorderStatus.UNSET:
                unsetBorders.append(idx)
        return unsetBorders

    def getAllUnsetBorders(self) -> list[int]:
        """
        Returns the list containing the indices of all `UNSET` borders.
        """
        unsetBorders: list[int] = []
        for idx in range(len(self.borders)):
            if self.borders[idx] == BorderStatus.UNSET:
                unsetBorders.append(idx)
        return unsetBorders
