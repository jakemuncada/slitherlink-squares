"""Board"""

from enums import BorderStatus


class Board:
    """The game board."""

    # The number of rows of the board.
    rows = 0

    # The number of columns of the board.
    cols = 0

    # The two-dimensional array containing the required sides of each cell.
    cells = [[]]

    # The two-dimensional array containing the status of each border.
    borders = [[]]

    def __init__(self, rows, cols, cells=None, borders=None):
        """
        Creates a game board.

        Args:
            rows (int): The number of rows of the board. Must be a positive number.
            rows (int): The number of columns of the board. Must be a positive number.
            cells ([[int]]): A two-dimensional array containing the required sides of each cell.
            borders ([[BorderStatus]]): A two-dimensional array containing the status
                of each border.
        """
        if rows <= 0 or cols <= 0:
            raise ValueError("Row or column must be a positive number.")

        if cells is not None and (len(cells) != rows or len(cells[0]) != cols):
            raise ValueError("The given cell data does not match " +
                             "the number of rows and columns of the board.")

        if borders is not None and (len(borders) != rows + 1 or len(borders[0]) != cols + 1):
            raise ValueError("The given border data has invalid number of rows and columns.")

        self.rows = rows
        self.cols = cols
        self.cells = cells if cells is not None else \
            [[None for _ in range(cols)] for _ in range(rows)]
        self.borders = borders if borders is not None else \
            [[BorderStatus.UNSET for _ in range(cols + 1)] for _ in range(rows + 1)]

    @classmethod
    def fromString(cls, rows, cols, cellDataString):
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

        idx = 0
        cells = []
        for _ in range(rows):
            rowArr = []
            for _ in range(cols):
                val = int(cellDataString[idx]) if cellDataString[idx] != "." else None
                rowArr.append(val)
                idx += 1
            cells.append(rowArr)

        return cls(rows, cols, cells)

    def copy(self):
        """Returns a deep copy of the Board."""
        return Board(self.rows, self.cols, self.cells, self.borders)

    def getUnsetBorders(self):
        """Returns the list of all `UNSET` borders. Each border is defined by a (row, col) tuple."""
        unsetBorders = []
        for i in range(len(self.borders)):
            for j in range(len(self.borders[i])):
                if self.borders[i][j] == BorderStatus.UNSET:
                    unsetBorders.append((i, j))
        return unsetBorders
