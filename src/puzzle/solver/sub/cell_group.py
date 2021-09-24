"""
This submodule contains the tools to solve the clues
regarding cell groups.
"""

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
    processedCells: set[tuple[int, int]] = set()

    adjUL = ((-1, 0), (0, -1))
    adjUR = ((-1, 0), (0, 1))
    adjLR = ((1, 0), (0, 1))
    adjLL = ((1, 0), (0, -1))
    adjust = (adjUL, adjUR, adjLR, adjLL)

    def _getCellAdjacentToCorner(row: int, col: int, dxn: DiagonalDirection) \
            -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        adjRow1, adjCol1 = adjust[dxn][0]
        adjRow2, adjCol2 = adjust[dxn][1]
        row1 = row + adjRow1
        col1 = col + adjCol1
        row2 = row + adjRow2
        col2 = col + adjCol2
        grp1 = 0
        grp2 = 0
        if 0 <= row1 < board.rows and 0 <= col1 < board.cols:
            grp1 = board.cellGroups[row1][col1]
        if 0 <= row2 < board.rows and 0 <= col2 < board.cols:
            grp2 = board.cellGroups[row2][col2]
        tuple1 = (row1, col1, grp1)
        tuple2 = (row2, col2, grp2)
        return (tuple1, tuple2)

    def _process(row: int, col: int, groupId: int):
        if (row, col) in processedCells:
            return

        if not BoardTools.isValidCellIdx(row, col):
            if groupId == 1:
                raise InvalidBoardException('Cannot set out of bounds as group 1.')
            return

        processedCells.add((row, col))
        if board.cellGroups[row][col] is not None and board.cellGroups[row][col] != groupId:
            raise InvalidBoardException(f'Failed to update cell goup of {row},{col}.')
        board.cellGroups[row][col] = groupId

        for dxn in CardinalDirection:
            bdrStat = board.getBorderStatus(row, col, dxn)
            adjRow, adjCol = BoardTools.getCellIdxOfAdjCell(row, col, dxn)
            if adjRow is not None and adjCol is not None:
                if bdrStat == BorderStatus.BLANK:
                    _process(adjRow, adjCol, groupId)
                elif bdrStat == BorderStatus.ACTIVE:
                    _process(adjRow, adjCol, 1 if groupId == 0 else 0)

            # Even though dxn is a CardinalDirection, we can treat its integer value
            # as an equivalent for DiagonalDirection and use it as a list index.

            # If the corner is POKE, the two adjacent cells' groups should be opposite.
            if board.cornerEntries[row][col][dxn] == CornerEntry.POKE:
                cell1, cell2 = _getCellAdjacentToCorner(row, col, dxn)
                row1, col1, grp1 = cell1
                row2, col2, grp2 = cell2
                if grp1 is not None:
                    _process(row2, col2, 1 if grp1 == 0 else 0)
                elif grp2 is not None:
                    _process(row1, col1, 1 if grp2 == 0 else 0)

            # If the corner is SMOOTH, the two adjacent cell's groups should be equal.
            elif board.cornerEntries[row][col][dxn] == CornerEntry.SMOOTH:
                cell1, cell2 = _getCellAdjacentToCorner(row, col, dxn)
                row1, col1, grp1 = cell1
                row2, col2, grp2 = cell2
                if grp1 is not None:
                    _process(row2, col2, grp1)
                elif grp2 is not None:
                    _process(row1, col1, grp2)

    for row in range(board.rows):
        col = 0
        if board.getBorderStatus(row, col, CardinalDirection.LEFT) == BorderStatus.BLANK:
            _process(row, col, 0)
        elif board.getBorderStatus(row, col, CardinalDirection.LEFT) == BorderStatus.ACTIVE:
            _process(row, col, 1)

        col = board.cols - 1
        if board.getBorderStatus(row, col, CardinalDirection.RIGHT) == BorderStatus.BLANK:
            _process(row, col, 0)
        elif board.getBorderStatus(row, col, CardinalDirection.RIGHT) == BorderStatus.ACTIVE:
            _process(row, col, 1)

    for col in range(board.cols):
        row = 0
        if board.getBorderStatus(row, col, CardinalDirection.TOP) == BorderStatus.BLANK:
            _process(row, col, 0)
        elif board.getBorderStatus(row, col, CardinalDirection.TOP) == BorderStatus.ACTIVE:
            _process(row, col, 1)

        row = board.rows - 1
        if board.getBorderStatus(row, col, CardinalDirection.BOT) == BorderStatus.BLANK:
            _process(row, col, 0)
        elif board.getBorderStatus(row, col, CardinalDirection.BOT) == BorderStatus.ACTIVE:
            _process(row, col, 1)