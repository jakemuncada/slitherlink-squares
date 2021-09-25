"""
This submodule contains the tools to solve the clues
regarding cell groups.
"""

from typing import Optional

from src.puzzle.board import Board
from src.puzzle.solver.solver import Solver
from src.puzzle.board_tools import BoardTools
from src.puzzle.solver.tools import SolverTools
from src.puzzle.solver.sub.poke import handleSmoothCorner, initiatePoke
from src.puzzle.enums import BorderStatus, CardinalDirection, \
    CornerEntry, DiagonalDirection, InvalidBoardException


def checkCellGroupClues(board: Board, prioCells: list[tuple[int, int]]) -> bool:
    """
    If the cell group ID of two adjacent cells are not equal,
    the border between them should be set to `ACTIVE`.
    If the cell group ID's are equal, the border should be set to `BLANK`.
    """
    updateCellGroups(board)

    foundMove = False
    def fromAdj(isAdjEqual): return BorderStatus.BLANK if isAdjEqual else BorderStatus.ACTIVE

    for row, col in prioCells:

        reqNum = board.cells[row][col]
        borderIndices = BoardTools.getCellBorders(row, col)
        countUnset, _, _ = SolverTools.getStatusCount(board, borderIndices)

        if countUnset == 0:
            continue

        topIdx, rightIdx, botIdx, leftIdx = borderIndices
        borderStats = [board.borders[bdrIdx] for bdrIdx in borderIndices]

        bdrTop = board.borders[topIdx]
        bdrRight = board.borders[rightIdx]
        bdrBot = board.borders[botIdx]
        bdrLeft = board.borders[leftIdx]

        grpOwn = board.cellGroups[row][col]
        adjCellGroups = board.getAdjCellGroups(row, col)
        grpTop, grpRight, grpBot, grpLeft = adjCellGroups

        _found = False
        if reqNum == 1:
            if grpTop == grpBot and grpTop is not None and grpBot is not None:
                _found = _found | Solver.setBorder(board, topIdx, BorderStatus.BLANK)
                _found = _found | Solver.setBorder(board, botIdx, BorderStatus.BLANK)
            elif grpTop != grpBot and grpTop is not None and grpBot is not None:
                _found = _found | Solver.setBorder(board, leftIdx, BorderStatus.BLANK)
                _found = _found | Solver.setBorder(board, rightIdx, BorderStatus.BLANK)

            if grpLeft == grpRight and grpLeft is not None and grpRight is not None:
                _found = _found | Solver.setBorder(board, leftIdx, BorderStatus.BLANK)
                _found = _found | Solver.setBorder(board, rightIdx, BorderStatus.BLANK)
            elif grpLeft != grpRight and grpLeft is not None and grpRight is not None:
                _found = _found | Solver.setBorder(board, topIdx, BorderStatus.BLANK)
                _found = _found | Solver.setBorder(board, botIdx, BorderStatus.BLANK)

        elif reqNum == 2:
            if (grpTop == grpBot and grpTop is not None) or \
                    (grpLeft == grpRight and grpLeft is not None):
                for dxn in DiagonalDirection:
                    _found = _found | initiatePoke(board, row, col, dxn)

        elif reqNum == 3:
            if grpTop == grpBot and grpTop is not None:
                _found = _found | Solver.setBorder(board, topIdx, BorderStatus.ACTIVE)
                _found = _found | Solver.setBorder(board, botIdx, BorderStatus.ACTIVE)
            if grpLeft == grpRight and grpLeft is not None:
                _found = _found | Solver.setBorder(board, leftIdx, BorderStatus.ACTIVE)
                _found = _found | Solver.setBorder(board, rightIdx, BorderStatus.ACTIVE)
            if grpTop is not None and grpBot is not None and grpTop != grpBot:
                _found = _found | Solver.setBorder(board, leftIdx, BorderStatus.ACTIVE)
                _found = _found | Solver.setBorder(board, rightIdx, BorderStatus.ACTIVE)
            if grpLeft is not None and grpRight is not None and grpLeft != grpRight:
                _found = _found | Solver.setBorder(board, topIdx, BorderStatus.ACTIVE)
                _found = _found | Solver.setBorder(board, botIdx, BorderStatus.ACTIVE)

        foundMove = foundMove or _found
        if _found:
            continue

        if grpOwn is not None:
            for i in range(4):
                bdrIdx = borderIndices[i]
                bdrStat = borderStats[i]
                adjGrp = adjCellGroups[i]
                if bdrStat == BorderStatus.UNSET and adjGrp is not None:
                    newStatus = fromAdj(grpOwn == adjGrp)
                    Solver.setBorder(board, bdrIdx, newStatus)
                    foundMove = True
            continue

        cornerStats = ((bdrTop, bdrLeft), (bdrTop, bdrRight), (bdrBot, bdrRight), (bdrBot, bdrLeft))
        cornerGrps = ((grpTop, grpLeft), (grpTop, grpRight), (grpBot, grpRight), (grpBot, grpLeft))

        for dxn in DiagonalDirection:
            bdrStat1, bdrStat2 = cornerStats[dxn]
            grp1, grp2 = cornerGrps[dxn]

            if bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.UNSET:
                if grp1 is not None and grp2 is not None:
                    if grp1 == grp2:
                        foundMove = foundMove | handleSmoothCorner(board, row, col, dxn)
                    else:
                        foundMove = foundMove | initiatePoke(board, row, col, dxn)

    return foundMove


def updateCellGroups(board: Board) -> None:
    """
    Update the cell islands information of the board.
    """
    for row in range(board.rows):
        for col in range(board.cols):
            # Process only the cells whose cell group is not yet known.
            if board.cellGroups[row][col] is not None:
                continue

            for dxn in CardinalDirection:
                # Look for the borders of this cell that are either BLANK or ACTIVE.
                bdrStat = board.getBorderStatus(row, col, dxn)
                if bdrStat == BorderStatus.UNSET:
                    continue

                # Get the group ID of the cell adjacent to this direction.
                adjRow, adjCol = BoardTools.getCellIdxOfAdjCell(row, col, dxn)
                grp = _getCellGroup(board, adjRow, adjCol)
                # If the group of the adjacent cell is also unknown, continue on.
                if grp is None:
                    continue

                # If the border is ACTIVE, this cell's group must be OPPOSITE to
                # the adjacent cell's group.
                if bdrStat == BorderStatus.ACTIVE:
                    _setCellGroup(board, row, col, 1 if grp == 0 else 0)

                # If the border is BLANK, this cell's group must be EQUAL to
                # the adjacent cell's group.
                elif bdrStat == BorderStatus.BLANK:
                    _setCellGroup(board, row, col, grp)

                # The following processing will involve corner entries,
                # so we don't need to do this for cloned boards.
                if board.isClone:
                    continue

                for dxn in DiagonalDirection:
                    # Look at the corners of this cell. If the corner entry is UNKNOWN,
                    # we proceed to the next corner.
                    if board.cornerEntries[row][col] == CornerEntry.UNKNOWN:
                        continue

                    # Get the indices of the cells adjacent to this corner.
                    cellIdx1, cellIdx2 = BoardTools.getCellIndicesAdjacentToCorner(row, col, dxn)
                    row1, col1 = cellIdx1
                    row2, col2 = cellIdx2
                    # Also, get their group ID.
                    grp1 = _getCellGroup(board, row1, col1)
                    grp2 = _getCellGroup(board, row2, col2)

                    # If the corner is POKE, then the two adjacent cells' group must be OPPOSITE.
                    if board.cornerEntries[row][col] == CornerEntry.POKE:
                        if grp1 is not None:
                            _setCellGroup(board, row2, col2, 1 if grp1 == 0 else 0)
                        elif grp2 is not None:
                            _setCellGroup(board, row1, col1, 1 if grp2 == 0 else 0)

                    # If the corner is SMOOTH, then the two adjacent cells' group must be EQUAL.
                    elif board.cornerEntries[row][col] == CornerEntry.SMOOTH:
                        if grp1 is not None:
                            _setCellGroup(board, row2, col2, grp1)
                        elif grp2 is not None:
                            _setCellGroup(board, row1, col1, grp2)


def _setCellGroup(board: Board, row: int, col: int, groupId: int) -> None:
    """
    Set the cell group of the given cell. Uses recursion to also set
    its adjacent cells' group IDs.

    Arguments:
        board: The board.
        row: The row index of the cell.
        col: The column index of the cell.
        groupId: The group ID to set the cell to.
    """
    if not BoardTools.isValidCellIdx(row, col):
        if groupId == 0:
            return
        raise InvalidBoardException('Cannot set the group ID of out of bounds to 1.')

    if board.cellGroups[row][col] is not None:
        if board.cellGroups[row][col] == groupId:
            return
        raise InvalidBoardException(f'Cannot set the group ID of {row},{col} '
                                    'to the opposite group ID.')

    board.cellGroups[row][col] = groupId

    for dxn in CardinalDirection:
        # Look for the borders of this cell that are either BLANK or ACTIVE.
        bdrStat = board.getBorderStatus(row, col, dxn)
        if bdrStat == BorderStatus.UNSET:
            continue

        # Get the index of the cell adjacent in this direction.
        # If it is out of bounds, continue on.
        adjRow, adjCol = BoardTools.getCellIdxOfAdjCell(row, col, dxn)
        if adjRow is None or adjCol is None:
            continue

        # If the border is ACTIVE, the adjacent cell group must be OPPOSITE
        # to this cell group.
        if bdrStat == BorderStatus.ACTIVE:
            _setCellGroup(board, adjRow, adjCol, 1 if groupId == 0 else 0)

        # If the border is ACTIVE, the adjacent cell group must be EQUAL
        # to this cell group.
        elif bdrStat == BorderStatus.BLANK:
            _setCellGroup(board, adjRow, adjCol, groupId)


def _getCellGroup(board: Board, row: int, col: int) -> Optional[int]:
    """
    Get the cell group of the target cell. If the cell index is out of bounds,
    the group ID is zero.
    """
    if row is None or col is None or not BoardTools.isValidCellIdx(row, col):
        return 0
    return board.cellGroups[row][col]
