"""
This module contains the BoardTools class
which has functions to calculate for various stuff involving the board.

These functions do not need the current state of the board;
the calculations hold true for all boards that have the same size (rows & cols).

The main advantage is that since the functions are deterministic,
the result can be cached.
"""

from functools import cache
from typing import Optional

from src.puzzle.enums import CardinalDirection, DiagonalDirection

class BoardTools:
    """
    Class containing various calculation methods involving the board.
    These functions do not need the current state of the board;
    the calculations hold true for all boards that have the same size (rows & cols).
    """

    def __init__(self, rows: int, cols: int) -> None:
        self.rows = rows
        self.cols = cols
        self.numBorders = _numBorders(rows, cols)

    def isValidCellIdx(self, row: int, col: int) -> bool:
        return _isValidCellIdx(self.rows, self.cols, row, col)

    def isValidBorderIdx(self, borderIdx: int) -> bool:
        return _isValidBorderIdx(self.rows, self.cols, borderIdx)

    def getCellIdxAtAdjCorner(self, row: int, col: int, dxn: DiagonalDirection) -> Optional[tuple[int, int]]:
        return _getCellIdxAtAdjCorner(self.rows, self.cols, row, col, dxn)

    def getBorderIdx(self, row: int, col: int, direction: CardinalDirection) -> int:
        return _getBorderIdx(self.cols, row, col, direction)

    def getCellBorders(self, row: int, col: int) -> tuple[int, int, int, int]:
        return _getCellBorders(self.cols, row, col)
    
    def isBorderHorizontal(self, borderIdx: int) -> bool:
        return _isBorderHorizontal(borderIdx)

    def getConnectedBorders(self, borderIdx: int) -> tuple[list[int], list[int]]:
        return _getConnectedBorders(self.rows, self.cols, borderIdx)

    def getConnectedBordersList(self, borderIdx: int) -> list[int]:
        return _getConnectedBordersList(self.rows, self.cols, borderIdx)

    def getCommonVertex(self, borderIdx1: int, borderIdx2: int) -> Optional[list[int]]:
        return _getCommonVertex(self.rows, self.cols, borderIdx1, borderIdx2)

    def getCornerBorderIndices(self, row: int, col: int, cornerDir: DiagonalDirection) -> tuple[int, int]:
        return _getCornerBorderIndices(self.cols, row, col, cornerDir)

    def getArms(self, row: int, col: int, cornerDir: DiagonalDirection) -> list[int]:
        return _getArms(self.rows, self.cols, row, col, cornerDir)

    def getArmsOfCell(self, row: int, col: int) \
        -> tuple[list[int], list[int], list[int], list[int]]:
        return _getArmsOfCell(self.rows, self.cols, row, col)


@cache
def _isValidCellIdx(rows: int, cols: int, row: int, col: int) -> bool:
    """
    Returns true if the given cell coordinates are valid.
    Returns false otherwise.
    """
    return row >= 0 and row < rows and col >= 0 and col < cols

@cache
def _isValidBorderIdx(rows: int, cols: int, borderIdx: int) -> bool:
    """
    Returns true if the given cell coordinates are valid.
    Returns false otherwise.
    """
    return borderIdx >= 0 and borderIdx < _numBorders(rows, cols)

@cache
def _numBorders(rows: int, cols: int) -> int:
    """
    Returns the number of borders in a given board
    with a certain amount of rows and columns.
    """
    return (((cols * 2) + 1) * rows) + cols

@cache
def _getCellIdxAtAdjCorner(rows: int, cols: int, row: int, col: int, \
    dxn: DiagonalDirection) -> Optional[tuple[int, int]]:
    """
    Get the cell index of the diagonally adjacent cell.

    Arguments:
        rows: The number of rows in the board.
        cols: The number of columns in the board.
        row: The cell's row index.
        col: The cell's column index.
        direction: The diagonal direction of the target adjacent cell.

    Returns:
        The row and column index of the target border.
        None if the target cell index is not valid.
    """
    if dxn == DiagonalDirection.ULEFT:
        targetRow = row - 1
        targetCol = col - 1
    elif dxn == DiagonalDirection.URIGHT:
        targetRow = row - 1
        targetCol = col + 1
    elif dxn == DiagonalDirection.LRIGHT:
        targetRow = row + 1
        targetCol = col + 1
    elif dxn == DiagonalDirection.LLEFT:
        targetRow = row + 1
        targetCol = col - 1
    else:
        raise ValueError(f'Invalid DiagonalDirection: {dxn}')

    if not _isValidCellIdx(rows, cols, targetRow, targetCol):
        return None
    return (targetRow, targetCol)

@cache
def _getBorderIdx(cols: int, row: int, col: int, direction: CardinalDirection) -> int:
    """
    Get the index of the target border.

    Arguments:
        cols: The number of columns in the board.
        row: The cell's row index.
        col: The cell's column index.
        direction: The direction of the target border.

    Returns:
        The index of the target border.
    """
    idx = ((cols * 2) + 1) * row
    if direction == CardinalDirection.TOP:
        idx += col
    elif direction == CardinalDirection.LEFT:
        idx += cols + col
    elif direction == CardinalDirection.RIGHT:
        idx += cols + col + 1
    elif direction == CardinalDirection.BOT:
        idx += (cols * 2) + 1 + col
    else:
        raise IndexError()
    return idx

@cache
def _getCellBorders(cols: int, row: int, col: int) -> tuple[int, int, int, int]:
    """
    Returns the border indices of the target cell's borders.

    Arguments:
        cols: The number of columns in the board.
        row: The row of the target cell.
        col: The column of the target cell.

    Returns:
        The border indices of the target cell's borders.
    """
    topBdr = _getBorderIdx(cols, row, col, CardinalDirection.TOP)
    rightBdr = _getBorderIdx(cols, row, col, CardinalDirection.RIGHT)
    botBdr = _getBorderIdx(cols, row, col, CardinalDirection.BOT)
    leftBdr = _getBorderIdx(cols, row, col, CardinalDirection.LEFT)
    return (topBdr, rightBdr, botBdr, leftBdr)

@cache
def _isBorderHorizontal(cols: int, borderIdx: int) -> bool:
    """
    Returns true if the target border is a horizontal border.
    Returns false if it is vertical.

    Arguments:
        cols: The number of columns in the board.
        borderIdx: The target border's index.

    Returns:
        True if the target border is a horizontal border. False otherwise.
    """
    isHorizontal = True
    thresholdIdx = cols
    while True:
        if borderIdx < thresholdIdx:
            break
        if isHorizontal:
            thresholdIdx += cols + 1
        else:
            thresholdIdx += cols
        isHorizontal = not isHorizontal
    return isHorizontal

@cache
def _getConnectedBorders(rows: int, cols: int, borderIdx: int) -> tuple[list[int], list[int]]:
    """
    Returns the list of borders connected to the target border.
    The connected borders are separated into two lists,
    one for each endpoint of the target border.

    Arguments:
        rows: The number of rows in the board.
        cols: The number of columns in the board.
        borderIdx: The target border's index.

    Returns:
        Two lists, each of which contains the indices of the borders
        connected to each endpoint.
    """
    leftTop: list[int] = []
    rightBot: list[int] = []

    if _isBorderHorizontal(cols, borderIdx):
        # Left-Above vertical
        if _isValidBorderIdx(rows, cols, borderIdx - (cols + 1)):
            leftTop.append(borderIdx - (cols + 1))
        # Left adjacent horizontal
        if _isBorderHorizontal(cols, borderIdx - 1):
            if _isValidBorderIdx(rows, cols, borderIdx - 1):
                leftTop.append(borderIdx - 1)
        # Left-Below vertical
        if _isValidBorderIdx(rows, cols, borderIdx + cols):
            leftTop.append(borderIdx + cols)

        # Right-Above vertical
        if _isValidBorderIdx(rows, cols, borderIdx - cols):
            rightBot.append(borderIdx - cols)
        # Right adjacent horizontal
        if _isBorderHorizontal(cols, borderIdx + 1):
            if _isValidBorderIdx(rows, cols, borderIdx + 1):
                rightBot.append(borderIdx + 1)
        # Right-Below vertical
        if _isValidBorderIdx(rows, cols, borderIdx + cols + 1):
            rightBot.append(borderIdx + cols + 1)
    else:
        # Above-Left horizontal
        if _isValidBorderIdx(rows, cols, borderIdx - (cols + 1)):
            if _isBorderHorizontal(cols, borderIdx - (cols + 1)):
                leftTop.append(borderIdx - (cols + 1))
        # Above adjacent vertical
        if _isValidBorderIdx(rows, cols, borderIdx - ((cols * 2) + 1)):
            leftTop.append(borderIdx - ((cols * 2) + 1))
        # Above-Right horizontal
        if _isValidBorderIdx(rows, cols, borderIdx - cols):
            if _isBorderHorizontal(cols, borderIdx - cols):
                leftTop.append(borderIdx - cols)

        # Below-Left horizontal
        if _isValidBorderIdx(rows, cols, borderIdx + cols):
            if _isBorderHorizontal(cols, borderIdx + cols):
                rightBot.append(borderIdx + cols)
        # Below adjacent vertical
        if _isValidBorderIdx(rows, cols, borderIdx + ((cols * 2) + 1)):
            rightBot.append(borderIdx + ((cols * 2) + 1))
        # Below-Right horizontal
        if _isValidBorderIdx(rows, cols, borderIdx + cols + 1):
            if _isBorderHorizontal(cols, borderIdx + cols + 1):
                rightBot.append(borderIdx + cols + 1)
    return (leftTop, rightBot)

@cache
def _getConnectedBordersList(rows: int, cols: int, borderIdx: int) -> list[int]:
    """
    Returns the list of borders connected to the target border.

    Arguments:
        rows: The number of rows in the board.
        cols: The number of columns in the board.
        borderIdx: The target border's index.

    Returns:
        The list of borders connected to the target border.
    """
    conn = _getConnectedBorders(rows, cols, borderIdx)
    return [bdr for bdr in conn[0] + conn[1]]


@cache
def _getCommonVertex(rows: int, cols: int, borderIdx1: int, borderIdx2: int) -> Optional[list[int]]:
    """
    Determines if the two given borders share a common vertex.
    Returns the indices of the borders found in that common vertex, if they do share a common vertex.
    Returns None if they don't.
    """
    conn = _getConnectedBorders(rows, cols, borderIdx1)
    if borderIdx2 in conn[0]:
        return [bdr for bdr in conn[0]]
    if borderIdx2 in conn[1]:
        return [bdr for bdr in conn[1]]
    return None

@cache
def _getCornerBorderIndices(cols: int, row: int, col: int, cornerDir: DiagonalDirection) -> tuple[int, int]:
    """
    Returns the indices of the two borders in the target corner direction.

    Arguments:
        cols: The number of columns in the board.
        row: The cell's row index.
        col: The cell's column index.
        cornerDir: The direction of the corner.

    Returns:
        The index of the target cell's corner.
    """
    if cornerDir == DiagonalDirection.ULEFT:
        d1 = CardinalDirection.TOP
        d2 = CardinalDirection.LEFT
    elif cornerDir == DiagonalDirection.URIGHT:
        d1 = CardinalDirection.TOP
        d2 = CardinalDirection.RIGHT
    elif cornerDir == DiagonalDirection.LRIGHT:
        d1 = CardinalDirection.BOT
        d2 = CardinalDirection.RIGHT
    elif cornerDir == DiagonalDirection.LLEFT:
        d1 = CardinalDirection.BOT
        d2 = CardinalDirection.LEFT
    
    border1 = _getBorderIdx(cols, row, col, d1)
    border2 = _getBorderIdx(cols, row, col, d2)
    return (border1, border2)

@cache
def _getArms(rows: int, cols: int, row: int, col: int, cornerDir: DiagonalDirection) -> list[int]:
    """
    Returns the arms of the cell at the target corner.
    
    Arguments:
        rows: The number of rows in the board.
        cols: The number of columns in the board.
        row: The cell's row index.
        col: The cell's column index.
        cornerDir: The target corner.

    Returns:
        The border indices of the arms of the cell at the target corner.
    """
    topBdrIdx = _getBorderIdx(cols, row, col, CardinalDirection.TOP)
    rightBdrIdx = _getBorderIdx(cols, row, col, CardinalDirection.RIGHT)
    botBdrIdx = _getBorderIdx(cols, row, col, CardinalDirection.BOT)
    leftBdrIdx = _getBorderIdx(cols, row, col, CardinalDirection.LEFT)

    if cornerDir == DiagonalDirection.ULEFT:
        conn = _getConnectedBorders(rows, cols, topBdrIdx)
        arms = [bdrIdx for bdrIdx in conn[0] if bdrIdx != topBdrIdx and bdrIdx != leftBdrIdx]
    elif cornerDir == DiagonalDirection.URIGHT:
        conn = _getConnectedBorders(rows, cols, topBdrIdx)
        arms = [bdrIdx for bdrIdx in conn[1] if bdrIdx != topBdrIdx and bdrIdx != rightBdrIdx]
    elif cornerDir == DiagonalDirection.LRIGHT:
        conn = _getConnectedBorders(rows, cols, botBdrIdx)
        arms = [bdrIdx for bdrIdx in conn[1] if bdrIdx != botBdrIdx and bdrIdx != rightBdrIdx]
    elif cornerDir == DiagonalDirection.LLEFT:
        conn = _getConnectedBorders(rows, cols, botBdrIdx)
        arms = [bdrIdx for bdrIdx in conn[0] if bdrIdx != botBdrIdx and bdrIdx != leftBdrIdx]
    else:
        raise ValueError(f'Invalid cornerDir: {cornerDir}')
    return arms

@cache
def _getArmsOfCell(rows: int, cols: int, row: int, col: int) \
    -> tuple[list[int], list[int], list[int], list[int]]:
    """
    Returns the arms of the cell at each corner.
    
    Arguments:
        rows: The number of rows in the board.
        cols: The number of columns in the board.
        row: The cell's row index.
        col: The cell's column index.

    Returns:
        The arms of the cell at each corner as a tuple.
        The corners are ordered as follows: `ULEFT`, `URIGHT`, `LRIGHT`, `LLEFT`.
    """
    if _isValidCellIdx(rows, cols, row, col):
        armsUL = _getArms(rows, cols, row, col, DiagonalDirection.ULEFT)
        armsUR = _getArms(rows, cols, row, col, DiagonalDirection.URIGHT)
        armsLR = _getArms(rows, cols, row, col, DiagonalDirection.LRIGHT)
        armsLL = _getArms(rows, cols, row, col, DiagonalDirection.LLEFT)
        return (armsUL, armsUR, armsLR, armsLL)
    raise IndexError(f'Cannot get arms of invalid cell index: {row},{col}')