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
from src.puzzle.enums import BorderStatus, CardinalDirection, CornerEntry, DiagonalDirection, InvalidBoardException


def isCellPokingAtDir(board: Board, cellInfo: CellInfo, dxn: DiagonalDirection) \
        -> list[DiagonalDirection]:
    """
    Determine if the cell is poking towards the given direction.

    Arguments:
        board: The board.
        cellInfo: The cell information.
        dxn: The given direction.
    """
    if board.cornerEntries[cellInfo.row][cellInfo.col][dxn] == CornerEntry.SMOOTH:
        return False

    if board.cornerEntries[cellInfo.row][cellInfo.col][dxn] == CornerEntry.POKE:
        return True

    bdrStat1 = board.borders[cellInfo.cornerBdrs[dxn][0]]
    bdrStat2 = board.borders[cellInfo.cornerBdrs[dxn][1]]

    if cellInfo.reqNum == 1 and cellInfo.bdrBlankCount == 2:
        if bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.UNSET:
            return True

    if cellInfo.reqNum == 2 and cellInfo.bdrActiveCount == 1 and cellInfo.bdrBlankCount == 1:
        if bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.UNSET:
            return True

    if (bdrStat1 == BorderStatus.ACTIVE and bdrStat2 == BorderStatus.BLANK) or \
            (bdrStat1 == BorderStatus.BLANK and bdrStat2 == BorderStatus.ACTIVE):
        return True

    if cellInfo.reqNum == 3:
        if cellInfo.bdrActiveCount > 1:
            bdrStat3 = board.borders[cellInfo.cornerBdrs[dxn.opposite()][0]]
            bdrStat4 = board.borders[cellInfo.cornerBdrs[dxn.opposite()][1]]
            if bdrStat3 == BorderStatus.ACTIVE and bdrStat4 == BorderStatus.ACTIVE:
                return True

    return False


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
    if board.isClone:
        return False

    foundMove = False
    _updateCornerEntries(board)
    for row in range(solver.rows):
        for col in range(solver.cols):
            cellInfo = CellInfo.init(board, row, col)
            if cellInfo.bdrUnsetCount > 0:
                countPoke = 0
                countSmooth = 0
                for dxn in DiagonalDirection:
                    if board.cornerEntries[row][col][dxn] == CornerEntry.POKE:
                        countPoke += 1
                        if handleCellPoke(solver, board, row, col, dxn):
                            foundMove = True
                    elif board.cornerEntries[row][col][dxn] == CornerEntry.SMOOTH:
                        countSmooth += 1
                        if solver.handleSmoothCorner(solver.board, cellInfo, dxn):
                            foundMove = True

                    if cellInfo.reqNum == 0 and countSmooth < 4:
                        raise InvalidBoardException('0-Cells should have four smooth corners.')
                    elif cellInfo.reqNum == 3 or cellInfo.reqNum == 1:
                        if countPoke > 2 or countSmooth > 2:
                            raise InvalidBoardException('1-Cells and 3-Cells cannot have more than '
                                                        'two poke corners or two smooth corners.')
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
    # is already ACTIVE, remove the other border on that corner.
    # Otherwise, if one border is already BLANK, activate the other border.
    bdrIdx1, bdrIdx2 = BoardTools.getCornerBorderIndices(row, col, dxn)
    bdrStat1 = board.borders[bdrIdx1]
    bdrStat2 = board.borders[bdrIdx2]
    if bdrStat1 == BorderStatus.ACTIVE:
        if Solver.setBorder(board, bdrIdx2, BorderStatus.BLANK):
            foundMove = True
    elif bdrStat2 == BorderStatus.ACTIVE:
        if Solver.setBorder(board, bdrIdx1, BorderStatus.BLANK):
            foundMove = True
    elif bdrStat1 == BorderStatus.BLANK:
        if Solver.setBorder(board, bdrIdx2, BorderStatus.ACTIVE):
            foundMove = True
    elif bdrStat2 == BorderStatus.BLANK:
        if Solver.setBorder(board, bdrIdx1, BorderStatus.ACTIVE):
            foundMove = True

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
        if initiatePoke(solver, board, row, col, dxn.opposite()):
            foundMove = True

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

    if not foundMove and (row == 0 or col == 0 or row == board.rows - 1 or col == board.cols - 1):
        if row == 0 and col == 0 and dxn == DiagonalDirection.ULEFT:
            raise InvalidBoardException('The board\'s UL corner cell cannot be poked from the ULEFT.')
        elif row == board.rows - 1 and col == 0 and dxn == DiagonalDirection.LLEFT:
            raise InvalidBoardException('The board\'s LL corner cell cannot be poked from the LLEFT.')
        elif row == 0 and col == board.cols - 1 and dxn == DiagonalDirection.URIGHT:
            raise InvalidBoardException('The board\'s UR corner cell cannot be poked from the URIGHT.')
        elif row == board.rows - 1 and col == board.cols - 1 and dxn == DiagonalDirection.LRIGHT:
            raise InvalidBoardException('The board\'s LR corner cell cannot be poked from the LRIGHT.')

        # If cell is on the topmost row and is poked from the UPPER LEFT/RIGHT.
        if row == 0:
            if dxn == DiagonalDirection.ULEFT and col - 1 >= 0:
                bdrIdx = BoardTools.getBorderIdx(row, col - 1, CardinalDirection.TOP)
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    foundMove = True
            elif dxn == DiagonalDirection.URIGHT and col + 1 < board.cols:
                bdrIdx = BoardTools.getBorderIdx(row, col + 1, CardinalDirection.TOP)
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    foundMove = True

        # If the cell is on the bottommost row and is poked from the LOWER LEFT/RIGHT.
        elif row == board.rows - 1:
            if dxn == DiagonalDirection.LRIGHT and col + 1 < board.cols:
                bdrIdx = BoardTools.getBorderIdx(row, col + 1, CardinalDirection.BOT)
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    foundMove = True
            elif dxn == DiagonalDirection.LLEFT and col - 1 >= 0:
                bdrIdx = BoardTools.getBorderIdx(row, col - 1, CardinalDirection.BOT)
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    foundMove = True

        # If the cell is on the leftmost column and is poked from the UPPER/LOWER LEFT.
        if col == 0:
            if dxn == DiagonalDirection.ULEFT and row - 1 >= 0:
                bdrIdx = BoardTools.getBorderIdx(row - 1, col, CardinalDirection.LEFT)
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    foundMove = True
            elif dxn == DiagonalDirection.LLEFT and row + 1 < board.rows:
                bdrIdx = BoardTools.getBorderIdx(row + 1, col, CardinalDirection.LEFT)
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    foundMove = True

        # If the cell is on the rightmost column and is poked from the UPPER/LOWER RIGHT.
        elif col == board.cols - 1:
            if dxn == DiagonalDirection.URIGHT and row - 1 >= 0:
                bdrIdx = BoardTools.getBorderIdx(row - 1, col, CardinalDirection.RIGHT)
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    foundMove = True
            elif dxn == DiagonalDirection.LRIGHT and row + 1 < board.rows:
                bdrIdx = BoardTools.getBorderIdx(row + 1, col, CardinalDirection.RIGHT)
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    foundMove = True

    return foundMove


def initiatePoke(solver: Solver, board: Board, origRow: int, origCol: int, dxn: DiagonalDirection) -> bool:
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
    if (origRow, origCol, dxn) in board.pokes:
        return False
    board.pokes.add((origRow, origCol, dxn))

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
