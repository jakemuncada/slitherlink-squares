"""
This submodule contains the tools to solve the clues
regarding poked cells.
"""

from typing import Optional

from src.puzzle.cell_info import CellInfo
from src.puzzle.board import Board
from src.puzzle.solver.solver import Solver
from src.puzzle.board_tools import BoardTools
from src.puzzle.solver.tools import SolverTools
from src.puzzle.enums import BorderStatus, CornerEntry, DiagonalDirection, InvalidBoardException


def solveUsingCornerEntryInfo(solver: Solver, board: Board) -> bool:
    """
    Update the CornerEntry types of each corner of each cell,
    then use that information to try to solve for their borders.

    This can only be performed on the main board, not on a clone.

    Arguments:
        solver: The solver.

    Returns:
        True if a move was found. False otherwise.
    """
    foundMove = False
    _updateCornerEntries(board)
    for row in range(solver.rows):
        for col in range(solver.cols):
            cellInfo = CellInfo.init(board, row, col)
            if cellInfo.bdrUnsetCount > 0:
                for dxn in DiagonalDirection:
                    if board.cornerEntries[row][col][dxn] == CornerEntry.POKE:
                        if initiatePoke(solver, board, row, col, dxn):
                            foundMove = True
                    elif board.cornerEntries[row][col][dxn] == CornerEntry.SMOOTH:
                        if solver.handleSmoothCorner(solver.board, cellInfo, dxn):
                            foundMove = True
    return foundMove


def _updateCornerEntries(board: Board) -> None:
    """
    Update the CornerEntry types of each corner of each cell.
    """
    updateFlag = True

    def setCornerEntry(cellIdx: Optional[tuple[int, int]], dxn: DiagonalDirection,
                        newVal: CornerEntry) -> bool:
        if cellIdx is None:
            return False
        row, col = cellIdx
        if board.cornerEntries[row][col][dxn] == CornerEntry.UNKNOWN:
            board.cornerEntries[row][col][dxn] = newVal
            return True
        elif board.cornerEntries[row][col][dxn] != newVal:
            raise InvalidBoardException(f'The corner entry of cell {row},{col} '
                                        f'at direction {dxn} cannot be set to {newVal}.')
        return False

    while updateFlag:
        updateFlag = False
        for row in range(board.rows):
            for col in range(board.cols):
                unknownDxn = None
                countPoke = 0
                countSmooth = 0
                countUnknown = 0
                for dxn in DiagonalDirection:
                    arms = BoardTools.getArms(row, col, dxn)
                    countUnset, countActive, _ = SolverTools.getStatusCount(board, arms)

                    if countUnset == 0:
                        targetCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
                        newVal = CornerEntry.SMOOTH if countActive % 2 == 0 else CornerEntry.POKE
                        updateFlag = updateFlag | setCornerEntry((row, col), dxn, newVal)
                        updateFlag = updateFlag | setCornerEntry(targetCellIdx, dxn.opposite(), newVal)

                    if board.cornerEntries[row][col][dxn] == CornerEntry.POKE:
                        countPoke += 1
                    elif board.cornerEntries[row][col][dxn] == CornerEntry.SMOOTH:
                        countSmooth += 1
                    elif board.cornerEntries[row][col][dxn] == CornerEntry.UNKNOWN:
                        countUnknown += 1
                        unknownDxn = dxn

                    if board.cornerEntries[row][col][dxn] != CornerEntry.UNKNOWN:
                        newVal = board.cornerEntries[row][col][dxn]
                        oppCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
                        updateFlag = updateFlag | setCornerEntry(oppCellIdx, dxn.opposite(), newVal)

                if countUnknown == 1:
                    newCornerEntry = CornerEntry.SMOOTH if countPoke % 2 == 0 else CornerEntry.POKE
                    updateFlag = updateFlag | setCornerEntry((row, col), unknownDxn, newCornerEntry)


def handleCellPoke(solver: Solver, board: Board, row: int, col: int, dxn: DiagonalDirection) -> bool:
    """
    Handle the situation when a cell is poked from a direction.

    Arguments:
        solver: The solver.
        board: The board.
        row: The row index of the poked cell.
        col: The column index of the poked cell.
        dxn: The direction of the poke when it enters the poked cell.

    Returns:
        True if a move was found. False otherwise.
    """
    foundMove = False
    reqNum = board.cells[row][col]

    board.cornerEntries[row][col][dxn] = CornerEntry.POKE
    if reqNum == 2:
        board.cornerEntries[row][col][dxn] = CornerEntry.POKE

    # If a cell is being poked at a particular corner and a border on that corner
    # is already active, remove the other border on that corner.
    bdrIdx1, bdrIdx2 = BoardTools.getCornerBorderIndices(row, col, dxn)
    bdrStat1 = board.borders[bdrIdx1]
    bdrStat2 = board.borders[bdrIdx2]
    if bdrStat1 == BorderStatus.ACTIVE:
        if Solver.setBorder(board, bdrIdx2, BorderStatus.BLANK):
            foundMove = True
    elif bdrStat2 == BorderStatus.ACTIVE:
        if Solver.setBorder(board, bdrIdx1, BorderStatus.BLANK):
            foundMove = True

    if foundMove:
        return True

    # If a 1-cell is poked, we know that its sole active border must be on that corner,
    # so we should remove the borders on the opposite corner.
    if reqNum == 1:
        blankBorders = BoardTools.getCornerBorderIndices(row, col, dxn.opposite())

        # The board is invalid if the border opposite from the poke direction is already ACTIVE.
        for bdrIdx in blankBorders:
            if Solver.setBorder(board, bdrIdx, BorderStatus.BLANK):
                foundMove = True

    # If a 2-cell is poked, poke the cell opposite from the original poke direction.
    elif reqNum == 2:
        bdrIdx1, bdrIdx2 = BoardTools.getCornerBorderIndices(row, col, dxn.opposite())
        # If 2-cell is poked, check if only one UNSET border is remaining on the opposite side.
        # If so, activate that border.
        if board.borders[bdrIdx1] == BorderStatus.BLANK:
            if Solver.setBorder(board, bdrIdx2, BorderStatus.ACTIVE):
                foundMove = True
        elif board.borders[bdrIdx2] == BorderStatus.BLANK:
            if Solver.setBorder(board, bdrIdx1, BorderStatus.ACTIVE):
                foundMove = True
        # Propagate the poke to the next cell
        foundMove = foundMove | initiatePoke(solver, board, row, col, dxn.opposite())

    # If a 3-cell is poked, the borders opposite the poked corner should be activated.
    elif reqNum == 3:
        borders = BoardTools.getCornerBorderIndices(row, col, dxn.opposite())
        for bdrIdx in borders:
            if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                foundMove = True
        # Check if there is an active arm from the poke direction.
        # If there is, remove the other arms from that corner.
        arms = BoardTools.getArms(row, col, dxn)
        countUnset, countActive, _ = SolverTools.getStatusCount(board, arms)

        # The board is invalid if the number of active arms is more than 1
        if countActive > 1:
            raise InvalidBoardException(f'A poked 3-cell cannot have more than two active arms: {row},{col}')

        if countActive == 1 and countUnset > 0:
            for bdrIdx in arms:
                if board.borders[bdrIdx] == BorderStatus.UNSET:
                    if Solver.setBorder(board, bdrIdx, BorderStatus.BLANK):
                        foundMove = True

    if not foundMove:
        # As a general case, check if the poke should activate a lone border.
        bdrIdx1, bdrIdx2 = BoardTools.getCornerBorderIndices(row, col, dxn)
        if board.borders[bdrIdx1] == BorderStatus.BLANK:
            if Solver.setBorder(board, bdrIdx2, BorderStatus.ACTIVE):
                foundMove = True
        elif board.borders[bdrIdx2] == BorderStatus.BLANK:
            if Solver.setBorder(board, bdrIdx1, BorderStatus.ACTIVE):
                foundMove = True

    if not foundMove:
        # Get all arms of the cell except for the direction that was poked.
        otherArms: list[int] = []
        for otherDxn in DiagonalDirection:
            if otherDxn == dxn:
                continue
            otherArms.extend(BoardTools.getArms(row, col, otherDxn))

        # Count the UNSET and ACTIVE arms from all those other arms.
        countUnset, countActive, _ = SolverTools.getStatusCount(board, otherArms)

        # If there is only one remaining UNSET arm, set it accordingly.
        if countUnset == 1:
            isActiveBordersEven = countActive % 2 == 0
            newStatus = BorderStatus.ACTIVE if isActiveBordersEven else BorderStatus.BLANK
            for bdrIdx in otherArms:
                if board.borders[bdrIdx] == BorderStatus.UNSET:
                    if Solver.setBorder(board, bdrIdx, newStatus):
                        foundMove = True

    return foundMove


def initiatePoke(solver:Solver, board: Board, origRow: int, origCol: int, dxn: DiagonalDirection) -> bool:
    """
    Initiate a poke on a diagonally adjacent cell from the origin cell.

    Arguments:
        solver: The solver.
        board: The board.
        origRow: The row index of the origin cell.
        origCol: The column index of the origin cell.
        dxn: The direction of the poke when it exits the origin cell.

    Returns:
        True if a move was found. False otherwise.
    """
    board.cornerEntries[origRow][origCol][dxn] = CornerEntry.POKE

    if dxn == DiagonalDirection.ULEFT:
        targetRow = origRow - 1
        targetCol = origCol - 1
    elif dxn == DiagonalDirection.URIGHT:
        targetRow = origRow - 1
        targetCol = origCol + 1
    elif dxn == DiagonalDirection.LRIGHT:
        targetRow = origRow + 1
        targetCol = origCol + 1
    elif dxn == DiagonalDirection.LLEFT:
        targetRow = origRow + 1
        targetCol = origCol - 1
    else:
        raise ValueError(f'Invalid DiagonalDirection: {dxn}')

    if BoardTools.isValidCellIdx(targetRow, targetCol):
        return handleCellPoke(solver, board, targetRow, targetCol, dxn.opposite())
    else:
        arms = BoardTools.getArms(origRow, origCol, dxn)
        assert len(arms) < 2, f'Did not expect outer cell to have more than 1 arm. ' \
            f'Cell ({origRow}, {origCol}) has {len(arms)} arms at the {dxn} corner.'
        for bdrIdx in arms:
            if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                return True
    return False