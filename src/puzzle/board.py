"""Board"""

from copy import deepcopy
from typing import Optional

from src.puzzle.board_tools import BoardTools
from src.puzzle.enums import BorderStatus, CardinalDirection, DiagonalDirection, OptInt


class Board:
    """
    The game board.
    """

    def __init__(self, rows: int, cols: int, cells: Optional[list[list[OptInt]]] = None,
                 borders: Optional[list[BorderStatus]] = None):
        """
        Creates a game board.

        Args:
            rows: The number of rows of the board. Must be a positive number.
            cols:  The number of columns of the board. Must be a positive number.
            cells: A two-dimensional array containing the required sides of each cell.
            borders: A two-dimensional array containing the status of each border.
        """
        if rows <= 0 or cols <= 0:
            raise ValueError('Row or column must be a positive number.')

        if cells is not None and (len(cells) != rows or len(cells[0]) != cols):
            raise ValueError('The given cell data does not match '
                             'the number of rows and columns of the board.')

        if borders is not None and (len(borders) != (((cols * 2) + 1) * rows) + cols):
            raise ValueError(f'The given border data has invalid length ({len(borders)}).')

        self.rows = rows
        self.cols = cols
        self.isClone = False

        self.cells = cells if cells is not None else \
            [[None for _ in range(cols)] for _ in range(rows)]

        self.borders = borders if borders is not None else \
            [BorderStatus.UNSET for _ in range((((cols * 2) + 1) * rows) + cols)]

        self.cellGroups = [[None for _ in range(cols)] for _ in range(rows)]

        self.reqCells = set()
        if cells is not None:
            for row in range(rows):
                for col in range(cols):
                    if cells[row][col] is not None:
                        self.reqCells.add((row, col))

    @property
    def isComplete(self) -> bool:
        """
        True if there are no more `UNSET` borders. False otherwise.
        """
        for bdr in self.borders:
            if bdr == BorderStatus.UNSET:
                return False
        return True

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

    def reset(self) -> None:
        """
        Reset the board to its initial state.
        """
        for borderIdx in range(len(self.borders)):
            self.borders[borderIdx] = BorderStatus.UNSET

        for row in range(self.rows):
            for col in range(self.cols):
                self.cellGroups[row][col] = None

    def clone(self):
        """
        Returns a deep copy of the Board.
        """
        cellsCopy = deepcopy(self.cells)
        bordersCopy = [bdrStatus for bdrStatus in self.borders]
        clonedBoard = Board(self.rows, self.cols, cellsCopy, bordersCopy)
        clonedBoard.isClone = True
        return clonedBoard

    ##################################################
    # BORDER STATUS SETTERS
    ##################################################

    def toggleBorder(self, borderIdx: int) -> None:
        """
        Toggle the target border's status.
        """
        if self.borders[borderIdx] == BorderStatus.UNSET:
            self.borders[borderIdx] = BorderStatus.ACTIVE
        elif self.borders[borderIdx] == BorderStatus.ACTIVE:
            self.borders[borderIdx] = BorderStatus.BLANK
        elif self.borders[borderIdx] == BorderStatus.BLANK:
            self.borders[borderIdx] = BorderStatus.UNSET

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
        idx = BoardTools.getBorderIdx(row, col, direction)
        return self.borders[idx]

    def getCornerStatus(self, row: int, col: int, dxn: DiagonalDirection) -> tuple[BorderStatus, BorderStatus]:
        """
        Get the statuses of the two borders connected to the specified corner direction.

        Arguments:
            row: The cell's row index.
            col: The cell's column index.
            dxn: The direction of the target corner.

        Returns:
            the statuses of the two borders connected to the specified corner direction.
        """
        bdr1, bdr2 = BoardTools.getCornerBorderIndices(row, col, dxn)
        stat1 = self.borders[bdr1]
        stat2 = self.borders[bdr2]
        return (stat1, stat2)

    def getArmsStatus(self, row: int, col: int, dxn: DiagonalDirection) -> list[BorderStatus]:
        """
        Get the statuses of the arms connected to the specified corner direction.

        Arguments:
            row: The cell's row index.
            col: The cell's column index.
            dxn: The direction of the target corner.

        Returns:
            the statuses of the arms connected to the specified corner direction.
        """
        arms = BoardTools.getArms(row, col, dxn)
        return [self.borders[bdrIdx] for bdrIdx in arms]

    def getAdjCellGroups(self, row: int, col: int) -> tuple[OptInt, OptInt, OptInt, OptInt]:
        """
        Get the cell groups of each adjacent cells.

        Arguments:
            row: The row index of the target cell.
            col: The column index of the target cell.

        Returns:
            The cell group of each adjacent cell.
        """
        adjCellGroups: list[OptInt] = []
        for dxn in CardinalDirection:
            adjRow, adjCol = BoardTools.getCellIdxOfAdjCell(row, col, dxn)
            if adjRow is not None and adjCol is not None:
                adjCellGroups.append(self.cellGroups[adjRow][adjCol])
            else:
                adjCellGroups.append(0)
        return tuple(adjCellGroups)
