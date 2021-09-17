"""
This module contains the functions that will fill-in
the initial solved-state of the board based on the cell numbers,
for example like 0-cells and adjacent 3-cells.
"""

from src.puzzle.board import Board
from src.puzzle.enums import BorderStatus, CardinalDirection, DiagonalDirection


def solveInit(board: Board, reqCells: set[tuple[int, int]]) -> None:
    """
    Fill in the initial solved-state of the board based on the cell numbers.

    Arguments:
        board: The board.
        reqCells: The set of cell indices that contain a required border number.

    Returns:
        True if all the borders were filled-in successfully.
        False if the given board configuration is invalid.
    """
    isSuccess = True

    for cellIdx in reqCells:
        row = cellIdx[0]
        col = cellIdx[1]
        reqNum = board.cells[row][col]

        if not isSuccess:
            return False

        cellBorders = board.tools.getCellBorders(row, col)

        if reqNum == 0:
            for bdrIdx in cellBorders:
                isSuccess = isSuccess and _setBorder(board, bdrIdx, BorderStatus.BLANK)

        elif reqNum == 3:
            isSuccess = isSuccess and _handleAdjacent3Cells(board, cellIdx, reqCells)
            isSuccess = isSuccess and _handleDiagonallyAdjacent3Cells(board, cellIdx, reqCells)


def _handleAdjacent3Cells(board: Board, cellIdx: tuple[int, int],
                          reqCells: set[tuple[int, int]]) -> bool:
    """
    Check and handle the case where the given 3-cell has an adjacent 3-cell.

    Arguments:
        board: The board.
        cellIdx: The cell index of the 3-cell.
        reqCells: The set of cell indices that contain a required border number.

    Returns:
        True if all the borders were filled-in successfully.
        False if the given board configuration is invalid.
    """
    row = cellIdx[0]
    col = cellIdx[1]
    cellBorders = board.tools.getCellBorders(row, col)
    topB, rightB, botB, leftB = cellBorders

    def _setAdj3CellBorders(dxn: CardinalDirection, other3CellIdx: tuple[int, int]) -> bool:
        other3CellRow = other3CellIdx[0]
        other3CellCol = other3CellIdx[1]
        otherCellBorders = board.tools.getCellBorders(other3CellRow, other3CellCol)
        bdrFilter = cellBorders + otherCellBorders

        if dxn == CardinalDirection.TOP:
            activeBorders = [topB, botB]
            conn = board.tools.getConnectedBordersList(topB)
            blankBorders = [bdr for bdr in conn if bdr not in bdrFilter]
        elif dxn == CardinalDirection.BOT:
            activeBorders = [topB, botB]
            conn = board.tools.getConnectedBordersList(botB)
            blankBorders = [bdr for bdr in conn if bdr not in bdrFilter]
        elif dxn == CardinalDirection.RIGHT:
            activeBorders = [leftB, rightB]
            conn = board.tools.getConnectedBordersList(rightB)
            blankBorders = [bdr for bdr in conn if bdr not in bdrFilter]
        elif dxn == CardinalDirection.LEFT:
            activeBorders = [leftB, rightB]
            conn = board.tools.getConnectedBordersList(leftB)
            blankBorders = [bdr for bdr in conn if bdr not in bdrFilter]

        _success = True
        for bdr in activeBorders:
            _success = _success and _setBorder(board, bdr, BorderStatus.ACTIVE)
        for bdr in blankBorders:
            _success = _success and _setBorder(board, bdr, BorderStatus.BLANK)
        return _success

    isSuccess = True
    # Check TOP for a 3-cell
    if (row - 1, col) in reqCells and board.cells[row - 1][col] == 3:
        isSuccess = isSuccess and _setAdj3CellBorders(CardinalDirection.TOP, (row - 1, col))
    # Check RIGHT for a 3-cell
    if (row, col + 1) in reqCells and board.cells[row][col + 1] == 3:
        isSuccess = isSuccess and _setAdj3CellBorders(CardinalDirection.RIGHT, (row, col + 1))
    # Check BOT for a 3-cell
    if (row + 1, col) in reqCells and board.cells[row + 1][col] == 3:
        isSuccess = isSuccess and _setAdj3CellBorders(CardinalDirection.BOT, (row + 1, col))
    # Check LEFT for a 3-cell
    if (row, col - 1) in reqCells and board.cells[row][col - 1] == 3:
        isSuccess = isSuccess and _setAdj3CellBorders(CardinalDirection.LEFT, (row, col - 1))

    return isSuccess


def _handleDiagonallyAdjacent3Cells(board: Board, cellIdx: tuple[int, int],
                                    reqCells: set[tuple[int, int]]) -> bool:
    """
    Check and handle the case where the given 3-cell has a diagonally adjacent 3-cell.

    Arguments:
        board: The board.
        cellIdx: The cell index of the 3-cell.
        reqCells: The set of cell indices that contain a required border number.

    Returns:
        True if all the borders were filled-in successfully.
        False if the given board configuration is invalid.
    """
    row = cellIdx[0]
    col = cellIdx[1]
    topB, rightB, botB, leftB = board.tools.getCellBorders(row, col)

    def _setCorner(dxn: DiagonalDirection) -> bool:
        armsUL, armsUR, armsLR, armsLL = board.tools.getArmsOfCell(row, col)

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

        _success = True
        for bdr in activeBorders:
            _success = _success and _setBorder(board, bdr, BorderStatus.ACTIVE)
        for bdr in blankBorders:
            _success = _success and _setBorder(board, bdr, BorderStatus.BLANK)
        return _success

    isSuccess = True

    # Check UL for a 3-cell
    if (row - 1, col - 1) in reqCells and board.cells[row - 1][col - 1] == 3:
        isSuccess = isSuccess and _setCorner(DiagonalDirection.LRIGHT)
    # Check UR for a 3-cell
    if (row - 1, col + 1) in reqCells and board.cells[row - 1][col + 1] == 3:
        isSuccess = isSuccess and _setCorner(DiagonalDirection.LLEFT)
    # Check LR for a 3-cell
    if (row + 1, col + 1) in reqCells and board.cells[row + 1][col + 1] == 3:
        isSuccess = isSuccess and _setCorner(DiagonalDirection.ULEFT)
    # Check LL for a 3-cell
    if (row + 1, col - 1) in reqCells and board.cells[row + 1][col - 1] == 3:
        isSuccess = isSuccess and _setCorner(DiagonalDirection.URIGHT)

    return isSuccess


def _setBorder(board: Board, borderIdx: int, newStatus: BorderStatus) -> bool:
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
        board.setBorderStatus(borderIdx, newStatus)
    else:
        return False
    return True
