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


##################################################
# INITIATE POKE
##################################################

def initiatePoke(board: Board, origRow: int, origCol: int, dxn: DiagonalDirection) -> bool:
    """
    Initiate a poke on a diagonally adjacent cell from the origin cell.

    Arguments:
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
    if board.cells[origRow][origCol] == 2:
        board.cornerEntries[origRow][origCol][dxn.opposite()] = CornerEntry.POKE

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
        return handleCellPoke(board, targetRow, targetCol, dxn.opposite())
    else:
        arms = BoardTools.getArms(origRow, origCol, dxn)
        assert len(arms) < 2, f'Did not expect outer cell to have more than 1 arm. ' \
            f'Cell ({origRow}, {origCol}) has {len(arms)} arms at the {dxn} corner.'
        for bdrIdx in arms:
            if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                return True
    return False


##################################################
# HANDLE CELL POKE
##################################################

def handleCellPoke(board: Board, row: int, col: int, dxn: DiagonalDirection) -> bool:
    """
    Handle the situation when a cell is poked from a direction.

    Arguments:
        board: The board.
        row: The row index of the poked cell.
        col: The column index of the poked cell.
        dxn: The direction of the poke when it enters the poked cell.

    Returns:
        True if a move was found. False otherwise.
    """
    foundMove = False
    reqNum = board.cells[row][col]
    oppoDxn = dxn.opposite()

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
        blankBorders = BoardTools.getCornerBorderIndices(row, col, oppoDxn)

        # The board is invalid if the border opposite from the poke direction is already ACTIVE.
        for bdrIdx in blankBorders:
            if Solver.setBorder(board, bdrIdx, BorderStatus.BLANK):
                foundMove = True

    # If a 2-cell is poked, poke the cell opposite from the original poke direction.
    elif reqNum == 2:
        bdrIdx1, bdrIdx2 = BoardTools.getCornerBorderIndices(row, col, oppoDxn)
        # If 2-cell is poked, check if only one UNSET border is remaining on the opposite side.
        # If so, activate that border.
        if board.borders[bdrIdx1] == BorderStatus.BLANK:
            if Solver.setBorder(board, bdrIdx2, BorderStatus.ACTIVE):
                foundMove = True
        elif board.borders[bdrIdx2] == BorderStatus.BLANK:
            if Solver.setBorder(board, bdrIdx1, BorderStatus.ACTIVE):
                foundMove = True
        # Propagate the poke to the next cell
        if initiatePoke(board, row, col, oppoDxn):
            foundMove = True

    # If a 3-cell is poked, the borders opposite the poked corner should be activated.
    elif reqNum == 3:
        borders = BoardTools.getCornerBorderIndices(row, col, oppoDxn)
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


##################################################
# HANDLE SMOOTH CORNER
##################################################

def handleSmoothCorner(board: Board, row: int, col: int, dxn: DiagonalDirection) -> bool:
    """
    Handle the situation when a cell's corner is known to be smooth.

    A smooth corner is a corner where a poke will never occur.
    This means that this corner either has two `ACTIVE` borders or two `BLANK` borders.

    Arguments:
        board: The board.
        row: The row index of the cell.
        col: The column index of the cell.
        dxn: The direction of the corner.

    Returns:
        True if a move was found. False otherwise.
    """
    foundMove = False
    reqNum = board.cells[row][col]

    board.cornerEntries[row][col][dxn] = CornerEntry.SMOOTH
    if reqNum == 2:
        board.cornerEntries[row][col][dxn.opposite()] = CornerEntry.SMOOTH

    cornerIdx1, cornerIdx2 = BoardTools.getCornerBorderIndices(row, col, dxn)
    cornerStat1 = board.borders[cornerIdx1]
    cornerStat2 = board.borders[cornerIdx2]

    # If the borders are already both ACTIVE or both BLANK, then there is nothing to do here.
    if cornerStat1 == cornerStat2 and cornerStat1 != BorderStatus.UNSET:
        return False

    # If one border is UNSET and the other is either ACTIVE or BLANK, set it accordingly.
    if cornerStat1 != cornerStat2:
        if cornerStat1 == BorderStatus.UNSET:
            Solver.setBorder(board, cornerIdx1, cornerStat2)
            return True
        elif cornerStat2 == BorderStatus.UNSET:
            Solver.setBorder(board, cornerIdx2, cornerStat1)
            return True
        else:
            raise InvalidBoardException(f'The cell {row},{col} should have a smooth {dxn} corner, '
                                        'but its corners are invalid.')

    # Determine if the smooth corner only has one UNSET arm.
    unsetArmCount = 0
    activeArmCount = 0
    unsetArmIdx = None
    for armIdx in BoardTools.getArms(row, col, dxn):
        if board.borders[armIdx] == BorderStatus.ACTIVE:
            activeArmCount += 1
        elif board.borders[armIdx] == BorderStatus.UNSET:
            unsetArmCount += 1
            unsetArmIdx = armIdx

    # If the smooth corner only has one UNSET arm, set it to accordingly.
    if unsetArmCount == 1:
        newStatus = BorderStatus.BLANK if activeArmCount % 2 == 0 else BorderStatus.ACTIVE
        if Solver.setBorder(board, unsetArmIdx, newStatus):
            return True

    # A smooth corner on a 1-cell always means that both borders are BLANK.
    if reqNum == 1:
        for bdrIdx in (cornerIdx1, cornerIdx2):
            if Solver.setBorder(board, bdrIdx, BorderStatus.BLANK):
                foundMove = True

    # A smooth corner on a 3-cell always means that both borders are ACTIVE.
    elif reqNum == 3:
        for bdrIdx in (cornerIdx1, cornerIdx2):
            if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                foundMove = True

    elif reqNum == 2:
        # Initiate pokes on the directions where its corners isn't smooth.
        if dxn == DiagonalDirection.ULEFT or dxn == DiagonalDirection.LRIGHT:
            if initiatePoke(board, row, col, DiagonalDirection.URIGHT):
                foundMove = True
            if initiatePoke(board, row, col, DiagonalDirection.LLEFT):
                foundMove = True
        elif dxn == DiagonalDirection.URIGHT or dxn == DiagonalDirection.LLEFT:
            if initiatePoke(board, row, col, DiagonalDirection.ULEFT):
                foundMove = True
            if initiatePoke(board, row, col, DiagonalDirection.LRIGHT):
                foundMove = True
        else:
            raise ValueError(f'Invalid DiagonalDirection: {dxn}')

        # Propagate the smoothing because if a 2-cell's corner is smooth, the opposite corner is also smooth.
        targetCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn.opposite())
        if targetCellIdx is not None:
            targetRow, targetCol = targetCellIdx
            if handleSmoothCorner(board, targetRow, targetCol, dxn):
                foundMove = True
        else:
            # If there is no diagonally adjacent cell, then this is an outer edge cell,
            # so we just directly remove the one arm at that direction.
            for armIdx in BoardTools.getArms(row, col, dxn.opposite()):
                if Solver.setBorder(board, armIdx, BorderStatus.BLANK):
                    return True

    return foundMove


##################################################
# IS CELL POKING AT GIVEN DIRECTION
##################################################

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

    oppoDxn = dxn.opposite()
    bdrStat1 = board.borders[cellInfo.cornerBdrs[dxn][0]]
    bdrStat2 = board.borders[cellInfo.cornerBdrs[dxn][1]]

    if (bdrStat1 == BorderStatus.ACTIVE and bdrStat2 == BorderStatus.BLANK) or \
            (bdrStat1 == BorderStatus.BLANK and bdrStat2 == BorderStatus.ACTIVE):
        return True

    if cellInfo.reqNum == 1 and cellInfo.bdrBlankCount == 2:
        if bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.UNSET:
            return True

    if cellInfo.reqNum == 2:
        # If the 2-cell has an ACTIVE and a BLANK border,
        if cellInfo.bdrActiveCount == 1 and cellInfo.bdrBlankCount == 1:
            # But the two borders on this corner are UNSET,
            # then the 2-cell is poking on this corner.
            if bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.UNSET:
                return True
        # Check if the 2-cell has an ACTIVE arm on both this corner and the opposite corner.
        arms = BoardTools.getArms(cellInfo.row, cellInfo.col, dxn)
        activeArmsThisDxn = len([idx for idx in arms if board.borders[idx] == BorderStatus.ACTIVE])
        oppoArms = BoardTools.getArms(cellInfo.row, cellInfo.col, oppoDxn)
        activeArmsOppoDxn = len([idx for idx in oppoArms if board.borders[idx] == BorderStatus.ACTIVE])

        if activeArmsThisDxn > 1 and activeArmsOppoDxn > 0:
            raise InvalidBoardException('2-cell is SMOOTH on one corner and POKE on the opposite corner.')
        if activeArmsThisDxn > 0 and activeArmsOppoDxn > 1:
            raise InvalidBoardException('2-cell is SMOOTH on one corner and POKE on the opposite corner.')

        if activeArmsThisDxn == 1 and activeArmsOppoDxn == 1:
            return True

    if cellInfo.reqNum == 3:
        if cellInfo.bdrActiveCount > 1:
            bdrStat3 = board.borders[cellInfo.cornerBdrs[oppoDxn][0]]
            bdrStat4 = board.borders[cellInfo.cornerBdrs[oppoDxn][1]]
            if bdrStat3 == BorderStatus.ACTIVE and bdrStat4 == BorderStatus.ACTIVE:
                return True

    return False


##################################################
# CHECK OUTER CELL POKING
##################################################

def checkOuterCellPoking(board: Board, cellInfo: CellInfo) -> bool:
    """
    Check for the special cases when the cells
    on the outer part of the board is poking their neighbor.

    Arguments:
        board: The board.
        cellInfo: The cell information.

    Returns:
        True if a move was found. False otherwise.
    """
    foundMove = False

    if cellInfo.bdrActiveCount == 0:
        return False

    row = cellInfo.row
    col = cellInfo.col

    # If the cell is a topmost cell, check if its TOP border is active.
    if row == 0 and cellInfo.topBdr == BorderStatus.ACTIVE:
        if col > 0:
            if handleCellPoke(board, row, col - 1, DiagonalDirection.URIGHT):
                foundMove = True
        if col < board.cols - 1:
            if handleCellPoke(board, row, col + 1, DiagonalDirection.ULEFT):
                foundMove = True

    # If the cell is a leftmost cell, check if its LEFT border is active.
    if col == 0 and cellInfo.leftBdr == BorderStatus.ACTIVE:
        if row > 0:
            if handleCellPoke(board, row - 1, col, DiagonalDirection.LLEFT):
                foundMove = True
        if row < board.rows - 1:
            if handleCellPoke(board, row + 1, col, DiagonalDirection.ULEFT):
                foundMove = True

    # If the cell is a rightmost cell, check if its RIGHT border is active.
    if col == board.cols - 1 and cellInfo.rightBdr == BorderStatus.ACTIVE:
        if row > 0:
            if handleCellPoke(board, row - 1, col, DiagonalDirection.LRIGHT):
                foundMove = True
        if row < board.rows - 1:
            if handleCellPoke(board, row + 1, col, DiagonalDirection.URIGHT):
                foundMove = True

    # If the cell is a bottommost cell, check if its BOT border is active.
    if row == board.rows - 1 and cellInfo.botBdr == BorderStatus.ACTIVE:
        if col > 0:
            if handleCellPoke(board, row, col - 1, DiagonalDirection.LRIGHT):
                foundMove = True
        if col < board.cols - 1:
            if handleCellPoke(board, row, col + 1, DiagonalDirection.LLEFT):
                foundMove = True

    return foundMove


##################################################
# SOLVE USING CORNER ENTRY INFORMATION
##################################################

def solveUsingCornerEntryInfo(board: Board) -> bool:
    """
    Update the CornerEntry types of each corner of each cell,
    then use that information to try to solve for their borders.

    This can only be performed on the main board, not on a clone.

    Arguments:
        board: The board.

    Returns:
        True if a move was found. False otherwise.
    """
    if board.isClone:
        return False

    foundMove = False
    _updateCornerEntries(board)
    for row in range(board.rows):
        for col in range(board.cols):
            reqNum = board.cells[row][col]

            hasUnsetBorder = False
            for dxn in CardinalDirection:
                if board.borders[BoardTools.getBorderIdx(row, col, dxn)] == BorderStatus.UNSET:
                    hasUnsetBorder = True
                    break

            if not hasUnsetBorder:
                continue

            countPoke = 0
            countSmooth = 0
            for dxn in DiagonalDirection:
                if board.cornerEntries[row][col][dxn] == CornerEntry.POKE:
                    countPoke += 1
                    if handleCellPoke(board, row, col, dxn):
                        foundMove = True
                elif board.cornerEntries[row][col][dxn] == CornerEntry.SMOOTH:
                    countSmooth += 1
                    if handleSmoothCorner(board, row, col, dxn):
                        foundMove = True

                if reqNum == 0 and countSmooth < 4:
                    raise InvalidBoardException('0-Cells should have four smooth corners.')
                elif reqNum == 3 or reqNum == 1:
                    if countPoke > 2 or countSmooth > 2:
                        raise InvalidBoardException('1-Cells and 3-Cells cannot have more than '
                                                    'two poke corners or two smooth corners.')
    return foundMove


##################################################
# UPDATE CORNER ENTRY INFORMATION
##################################################

def _updateCornerEntries(board: Board) -> None:
    """
    Update the CornerEntry types of each corner of each cell.
    """
    # When updateFlag is true, it means that we updated
    # a corner entry on the previous run, so we need to look at the board again
    # to see if we can use that as a clue and update another cell.
    # We initialize it to True so that we can start the first round.
    updateFlag = True

    # A set of cell indices that already has no more UNKNOWN corner.
    skipCells: set[tuple[int, int]] = set()

    # If updateFlag is false, we did not find a cell to update
    # on the previous run, so we stop the loop.
    while updateFlag:
        board.updateCellGroupCount += 1
        updateFlag = False
        # Loop through all the cells.
        for row in range(board.rows):
            for col in range(board.cols):
                if (row, col) in skipCells:
                    continue

                unknownDxn = None
                countPoke = 0
                countUnknown = 0
                reqNum = board.cells[row][col]
                # Loop through all the corners of the cell.
                for dxn in DiagonalDirection:
                    # Count the cell's ACTIVE and UNSET arms at this corner.
                    oppoDxn = dxn.opposite()

                    # If this corner has no UNSET arm, then this corner is either POKE or SMOOTH
                    # depending on the number of ACTIVE arms on this same corner.
                    if board.cornerEntries[row][col][dxn] == CornerEntry.UNKNOWN:
                        arms = BoardTools.getArms(row, col, dxn)
                        countUnset, countActive, _ = SolverTools.getStatusCount(board, arms)
                        if countUnset == 0:
                            # If this corner has ODD number of ACTIVE arms, then it is POKE.
                            # Else, if it has EVEN number of ACTIVE arms, then it is SMOOTH.
                            newVal = CornerEntry.SMOOTH if countActive % 2 == 0 else CornerEntry.POKE
                            if _setCornerEntry(board, (row, col), dxn, newVal):
                                updateFlag = True

                    if reqNum == 2:
                        # If the cell is a 2-cell and this corner is known to be POKE/SMOOTH,
                        # also set the opposite corner to be equal to this corner.
                        if board.cornerEntries[row][col][dxn] != CornerEntry.UNKNOWN:
                            newVal = board.cornerEntries[row][col][dxn]
                            if _setCornerEntry(board, (row, col), oppoDxn, newVal):
                                updateFlag = True

                            # If the cell is a 2-cell and this corner is SMOOTH,
                            # then the two adjacent corners should be POKE.
                            if board.cornerEntries[row][col][dxn] == CornerEntry.SMOOTH:
                                for adjDxn in dxn.adjacent():
                                    if _setCornerEntry(board, (row, col), adjDxn, CornerEntry.POKE):
                                        updateFlag = True

                    # If this corner is a POKE/SMOOTH, the corresponding corner
                    # of the diagonally adjacent cell should also be updated.
                    if board.cornerEntries[row][col][dxn] != CornerEntry.UNKNOWN:
                        newVal = board.cornerEntries[row][col][dxn]
                        oppCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
                        if _setCornerEntry(board, oppCellIdx, oppoDxn, newVal):
                            updateFlag = True

                    # Count the number of POKE and UNKNOWN corners of the cell
                    # (to be used outside of this DiagonalDirection loop).
                    if board.cornerEntries[row][col][dxn] == CornerEntry.POKE:
                        countPoke += 1
                    elif board.cornerEntries[row][col][dxn] == CornerEntry.UNKNOWN:
                        countUnknown += 1
                        unknownDxn = dxn

                # Now that all the corners of the cell have been processed,
                # we look at the number of UNKNOWN and POKE corners.

                # If the cell only has one UNKNOWN corner,
                # we can already deduce if it is POKE or SMOOTH.
                if countUnknown == 1:
                    # The number of POKE corners of a cell should always be EVEN.
                    # So we set the UNKNOWN corner to POKE such that
                    # the total POKE corners will be EVEN.
                    newCornerEntry = CornerEntry.SMOOTH if countPoke % 2 == 0 else CornerEntry.POKE
                    _setCornerEntry(board, (row, col), unknownDxn, newCornerEntry)
                    updateFlag = True

                # If this cell has no UNKNOWN corners,
                # skip processing it on the subsequent runs.
                if countUnknown == 0:
                    skipCells.add((row, col))


def _setCornerEntry(board: Board, cellIdx: Optional[tuple[int, int]],
                    dxn: DiagonalDirection, newVal: CornerEntry) -> bool:
    """
    Set the specified corner entry.

    Arguments:
        board: The board.
        cellIdx: The index of the cell. May be None.
        dxn: The direction of the corner to set.
        newVal: The new CornerEntry value.

    Returns:
        True if a cell was successfully changed from UNSET to the new value.
        False otherwise.
    """
    if cellIdx is None:
        return False
    row, col = cellIdx
    if board.cornerEntries[row][col][dxn] == newVal:
        return False
    if board.cornerEntries[row][col][dxn] == CornerEntry.UNKNOWN:
        board.cornerEntries[row][col][dxn] = newVal
        return True
    raise InvalidBoardException(f'The corner entry of cell {row},{col} '
                                f'at direction {dxn} cannot be set to {newVal}.')
