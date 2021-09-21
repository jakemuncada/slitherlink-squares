"""
This Solver submodule contains the tools to solve the clues
regarding continuous unset borders.
"""

from src.puzzle.board import Board
from src.puzzle.cell_info import CellInfo
from src.puzzle.solver.solver import Solver
from src.puzzle.board_tools import BoardTools
from src.puzzle.enums import BorderStatus, DiagonalDirection, InvalidBoardException


def checkCellForContinuousUnsetBorders(solver: Solver, board: Board, cellInfo: CellInfo) -> bool:
    """
    Check and handle the case when the given cell has continuous unset borders.
    Only cells which have number requirements will be processed.

    Arguments:
        solver: The solver.
        board: The board.
        cellInfo: The cell information.

    Returns:
        True if a move was found. False otherwise.
    """
    if cellInfo.bdrUnsetCount < 2:
        return False

    if cellInfo.reqNum is None or cellInfo.reqNum == 0:
        return False

    row = cellInfo.row
    col = cellInfo.col

    # Get the border indices of the cell's corners and arms.
    corners: list[tuple[int, int]] = []
    arms: list[list[int]] = []
    for dxn in DiagonalDirection:
        corners.append(BoardTools.getCornerBorderIndices(row, col, dxn))
        arms.append(BoardTools.getArms(row, col, dxn))

    # Determine whether each corner forms continuous unset borders.
    # Also get the number of corners where continous unset borders were found.
    # Also get if there are such corners that are adjacent/opposite.
    cornersStatus, count = _getCornersStatus(board, corners, arms)

    # If there are no corners with continuous unset borders, return False.
    if count == 0:
        return False

    # If all corners have continous unset borders, the board is invalid.
    if count == 4:
        raise InvalidBoardException('Found continous unset borders on all four corners.')

    if cellInfo.reqNum == 1:
        return _process1Cell(board, solver, cellInfo, corners, cornersStatus)
    elif cellInfo.reqNum == 2:
        return _process2Cell(board, solver, cellInfo, corners, cornersStatus)
    elif cellInfo.reqNum == 3:
        return _process3Cell(board, solver, cellInfo, corners, cornersStatus)

    raise AssertionError('Impossible to reach here.')


def _process1Cell(board: Board, solver: Solver, cellInfo: CellInfo, \
    corners: list[tuple[int, int]], cornersStatus: tuple[bool, bool, bool, bool]) -> bool:
    """
    Process the 1-cell.

    Arguments:
        board: The board.
        solver: The solver.
        corners: The border indices of the cell's corners.
        cornersStatus: The continuous-unset status of each corner.
        
    Returns:
        True if a move was found. False otherwise.
    """
    foundMove = False
    for dxn in DiagonalDirection:
        if cornersStatus[dxn]:
            # Smooth this corner and poke the opposite corner.
            solver.handleSmoothCorner(board, cellInfo, dxn)
            solver.initiatePoke(board, cellInfo.row, cellInfo.col, dxn.opposite())

            # If the 1-cell has continuous borders, set them to BLANK.
            Solver.setBorder(board, corners[dxn][0], BorderStatus.BLANK)
            Solver.setBorder(board, corners[dxn][1], BorderStatus.BLANK)
            # Return true because we know we have changed an UNSET border to BLANK.
            foundMove = True
    return foundMove


def _process2Cell(board: Board, solver: Solver, cellInfo: CellInfo, corners: list[tuple[int, int]], \
    cornersStatus: tuple[bool, bool, bool, bool]) -> bool:
    """
    Process the 2-cell.

    Arguments:
        board: The board.
        solver: The solver.
        cellInfo: The cell information.
        corners: The border indices of the cell's corners.
        arms: The border indices of the cell's arms at each corner.
        cornersStatus: The continuous-unset status of each corner.
        
    Returns:
        True if a move was found. False otherwise.
    """
    foundMove = False
    for dxn in DiagonalDirection:
        if cornersStatus[dxn]:

            # Smooth this corner and the opposite corner.
            solver.handleSmoothCorner(board, cellInfo, dxn)
            solver.handleSmoothCorner(board, cellInfo, dxn.opposite())
            
            # If there is a BLANK border on the opposite corner,
            # set the continous unset borders to ACTIVE.
            if cellInfo.bdrBlankCount > 1:
                Solver.setBorder(board, corners[dxn][0], BorderStatus.ACTIVE)
                Solver.setBorder(board, corners[dxn][1], BorderStatus.ACTIVE)
                return True

            # If there is an ACTIVE border on the opposite corner,
            # set the continous unset borders to BLANK.
            elif cellInfo.bdrActiveCount > 1:
                Solver.setBorder(board, corners[dxn][0], BorderStatus.BLANK)
                Solver.setBorder(board, corners[dxn][1], BorderStatus.BLANK)
                return True
            
    return foundMove


def _process3Cell(board: Board, solver: Solver, cellInfo: CellInfo, \
    corners: list[tuple[int, int]], cornersStatus: tuple[bool, bool, bool, bool]) -> bool:
    """
    Process the 3-cell.

    Arguments:
        board: The board.
        solver: The solver.
        corners: The border indices of the cell's corners.
        arms: The border indices of the cell's arms at each corner.
        cornersStatus: The continuous-unset status of each corner.
        
    Returns:
        True if a move was found. False otherwise.
    """
    foundMove = False
    for dxn in DiagonalDirection:
        if cornersStatus[dxn]:
            # If the 3-cell has continuous borders, set them to ACTIVE.
            Solver.setBorder(board, corners[dxn][0], BorderStatus.ACTIVE)
            Solver.setBorder(board, corners[dxn][1], BorderStatus.ACTIVE)

            # Smooth this corner and poke the opposite corner.
            solver.handleSmoothCorner(board, cellInfo, dxn)
            solver.initiatePoke(board, cellInfo.row, cellInfo.col, dxn.opposite())

            # Return true because we know we have changed an UNSET border to ACTIVE.
            foundMove = True
    return foundMove


def _getCornersStatus(board: Board, corners: list[tuple[int, int]], arms: list[list[int]]) \
     -> tuple[tuple[bool, bool, bool, bool], int]:
    """
    Determine if the cell's corners are continuous `UNSET` borders.

    Arguments:
        board: The board.
        corners: The border indices of the cell's corners at each direction.
        arms: The border indices of the cell's arms at each direction.

    Returns:
        A tuple with the following information:
            1) A list of bools signifying whether each corner has a continous unset border.
            2) The number of continous unset corners.
    """
    cornersStatus: list[bool] = []
    count = 0

    for dxn in DiagonalDirection:
        bdr1, bdr2 = corners[dxn]
        if board.borders[bdr1] == BorderStatus.UNSET and \
            board.borders[bdr2] == BorderStatus.UNSET:

            if all(board.borders[armIdx] == BorderStatus.BLANK for armIdx in arms[dxn]):
                cornersStatus.append(True)
                count += 1
            else:
                cornersStatus.append(False)
        else:
            cornersStatus.append(False)
        
    return (cornersStatus, count)
        