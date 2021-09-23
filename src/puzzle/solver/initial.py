"""
This module contains the functions that will fill-in
the initial solved-state of the board based on the cell numbers,
for example like 0-cells and adjacent 3-cells.
"""

from src.puzzle.board import Board
from src.puzzle.board_tools import BoardTools
from src.puzzle.enums import BorderStatus, CardinalDirection, DiagonalDirection


def solveInit(board: Board) -> None:
    """
    Fill in the initial solved-state of the board based on the cell numbers.

    Arguments:
        board: The board.
    """
    for row, col in board.reqCells:
        cellBorders = BoardTools.getCellBorders(row, col)

        if board.cells[row][col] == 0:
            for bdrIdx in cellBorders:
                _setBorder(board, bdrIdx, BorderStatus.BLANK)

        elif board.cells[row][col] == 3:
            _handleAdjacent3Cells(board, row, col)
            _handleDiagonal3Cells(board, row, col)


def _handleAdjacent3Cells(board: Board, row: int, col: int) -> None:
    """
    Check and handle the case where the given 3-cell has an adjacent 3-cell.

    Arguments:
        board: The board.
        row: The row index of the 3-cell.
        col: The column index of the 3-cell.
    """
    cellBorders = BoardTools.getCellBorders(row, col)
    topB, rightB, botB, leftB = cellBorders

    def _setAdj3CellBorders(dxn: CardinalDirection, other3CellIdx: tuple[int, int]) -> None:
        other3CellRow = other3CellIdx[0]
        other3CellCol = other3CellIdx[1]
        otherCellBorders = BoardTools.getCellBorders(other3CellRow, other3CellCol)
        bdrFilter = cellBorders + otherCellBorders

        if dxn == CardinalDirection.TOP:
            activeBorders = [topB, botB]
            conn = BoardTools.getConnectedBordersList(topB)
            blankBorders = [bdr for bdr in conn if bdr not in bdrFilter]
        elif dxn == CardinalDirection.BOT:
            activeBorders = [topB, botB]
            conn = BoardTools.getConnectedBordersList(botB)
            blankBorders = [bdr for bdr in conn if bdr not in bdrFilter]
        elif dxn == CardinalDirection.RIGHT:
            activeBorders = [leftB, rightB]
            conn = BoardTools.getConnectedBordersList(rightB)
            blankBorders = [bdr for bdr in conn if bdr not in bdrFilter]
        elif dxn == CardinalDirection.LEFT:
            activeBorders = [leftB, rightB]
            conn = BoardTools.getConnectedBordersList(leftB)
            blankBorders = [bdr for bdr in conn if bdr not in bdrFilter]

        for bdr in activeBorders:
            _setBorder(board, bdr, BorderStatus.ACTIVE)
        for bdr in blankBorders:
            _setBorder(board, bdr, BorderStatus.BLANK)

    # Check TOP for a 3-cell
    if (row - 1, col) in board.reqCells and board.cells[row - 1][col] == 3:
        _setAdj3CellBorders(CardinalDirection.TOP, (row - 1, col))
    # Check RIGHT for a 3-cell
    if (row, col + 1) in board.reqCells and board.cells[row][col + 1] == 3:
        _setAdj3CellBorders(CardinalDirection.RIGHT, (row, col + 1))
    # Check BOT for a 3-cell
    if (row + 1, col) in board.reqCells and board.cells[row + 1][col] == 3:
        _setAdj3CellBorders(CardinalDirection.BOT, (row + 1, col))
    # Check LEFT for a 3-cell
    if (row, col - 1) in board.reqCells and board.cells[row][col - 1] == 3:
        _setAdj3CellBorders(CardinalDirection.LEFT, (row, col - 1))


def _handleDiagonal3Cells(board: Board, row: int, col: int) -> None:
    """
    Check and handle the case where the given 3-cell
    has a 3-cell diagonal from it. There may be some 2-cells
    in between the two 3-cells.

    Arguments:
        board: The board.
        row: The row index of the 3-cell.
        col: The column index of the 3-cell.
    """
    topB, rightB, botB, leftB = BoardTools.getCellBorders(row, col)

    def _setCorner(dxn: DiagonalDirection) -> None:
        armsUL, armsUR, armsLR, armsLL = BoardTools.getArmsOfCell(row, col)

        if dxn == DiagonalDirection.ULEFT:
            activeBorders = (topB, leftB)
            blankBorders = armsUL
        elif dxn == DiagonalDirection.URIGHT:
            activeBorders = (topB, rightB)
            blankBorders = armsUR
        elif dxn == DiagonalDirection.LRIGHT:
            activeBorders = (botB, rightB)
            blankBorders = armsLR
        elif dxn == DiagonalDirection.LLEFT:
            activeBorders = (botB, leftB)
            blankBorders = armsLL

        for bdr in activeBorders:
            _setBorder(board, bdr, BorderStatus.ACTIVE)
        for bdr in blankBorders:
            _setBorder(board, bdr, BorderStatus.BLANK)

    # Check UL for a 3-cell
    if _hasDiagonal3Cell(board, row - 1, col - 1, DiagonalDirection.ULEFT):
        _setCorner(DiagonalDirection.LRIGHT)
    # Check UR for a 3-cell
    if _hasDiagonal3Cell(board, row - 1, col + 1, DiagonalDirection.URIGHT):
        _setCorner(DiagonalDirection.LLEFT)
    # Check LR for a 3-cell
    if _hasDiagonal3Cell(board, row + 1, col + 1, DiagonalDirection.LRIGHT):
        _setCorner(DiagonalDirection.ULEFT)
    # Check LL for a 3-cell
    if _hasDiagonal3Cell(board, row + 1, col - 1, DiagonalDirection.LLEFT):
        _setCorner(DiagonalDirection.URIGHT)


def _hasDiagonal3Cell(board: Board, row: int, col: int, dxn: DiagonalDirection) -> bool:
    """
    Returns true if the given cell is a 3-cell. Will propagate the checking
    if the given cell is a 2-cell.
    """
    if not (row, col) in board.reqCells:
        return False

    if board.cells[row][col] == 3:
        return True

    if board.cells[row][col] != 2:
        return False

    nextCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
    if nextCellIdx is None:
        return False

    return _hasDiagonal3Cell(board, nextCellIdx[0], nextCellIdx[1], dxn)


def _setBorder(board: Board, borderIdx: int, newStatus: BorderStatus) -> None:
    """
    Set the border to a new status.

    Arguments:
        board: The board.
        borderIdx: The target border's index.
        newStatus: The new border status.

    Returns:
        True if all the border was either `UNSET` or was already set to the target status.
        False otherwise.
    """
    if board.borders[borderIdx] == newStatus:
        pass
    elif board.borders[borderIdx] == BorderStatus.UNSET:
        board.borders[borderIdx] = newStatus
