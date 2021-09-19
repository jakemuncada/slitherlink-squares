"""
This module contains functions for solving the board.
"""

from typing import Union

from src.puzzle.board import Board
from src.puzzle.cell_info import CellInfo
from src.puzzle.enums import BorderStatus, CardinalDirection, DiagonalDirection, InvalidBoardException, OptInt


class SolverTools:
    """
    Class containing functions to help in solving the board.
    """

    def __init__(self) -> None:
        pass

    def getStatusCount(self, board: Board, bdrIdxList: Union[list[int], set[int], tuple]) \
            -> tuple[int, int, int]:
        """
        Returns the number of `UNSET`, `ACTIVE` and `BLANK` borders
        in that particular order.

        Arguments:
            board: The board.
            bdrIdxList: The list of target border indices.

        Returns:
            The number of `UNSET`, `ACTIVE` and `BLANK` borders as a tuple.
        """
        countUnset = 0
        countActive = 0
        countBlank = 0
        for idx in bdrIdxList:
            if board.borders[idx] == BorderStatus.UNSET:
                countUnset += 1
            elif board.borders[idx] == BorderStatus.ACTIVE:
                countActive += 1
            elif board.borders[idx] == BorderStatus.BLANK:
                countBlank += 1
        return (countUnset, countActive, countBlank)

    def isAdjCellReqNumEqualTo(self, board: Board, row: int, col: int,
                               dxn: CardinalDirection, query: OptInt) -> bool:
        """
        Get the cell index of the adjacent cell and return true
        if it matches the query.

        Arguments:
            board: The board.
            row: The cell's row index.
            col: The cell's column index.
            direction: The direction of the target adjacent cell.
            query: The query.

        Returns:
            True if the adjacent cell's reqNum matches the query.
        """
        adjRow, adjCol = board.tools.getCellIdxOfAdjCell(row, col, dxn)
        if adjRow is None or adjCol is None:
            return False
        return board.cells[adjRow][adjCol] == query

    def isContinuous(self, board: Board, borderIdx1: int, borderIdx2: int) -> bool:
        """
        Returns true if the two borders are continuous. Returns false otherwise.
        Borders are continuous if all of the conditions below are true:
            - The two borders are not `BLANK`.
            - The two borders share a common vertex.
            - All the other borders sharing that vertex are `BLANK`.

        Arguments:
            board: The board.
            borderIdx1: The index of the first target border.
            borderIdx2: The index of the second target border.

        Returns:
            True if the two borders are continuous. False otherwise.
        """
        if not board.tools.isValidBorderIdx(borderIdx1):
            return False

        if not board.tools.isValidBorderIdx(borderIdx2):
            return False

        # The two borders should not be `BLANK`.
        if board.borders[borderIdx1] == BorderStatus.BLANK:
            return False
        if board.borders[borderIdx2] == BorderStatus.BLANK:
            return False

        # Check that the two borders are connected (share a common vertex).
        commonBorders = board.tools.getCommonVertex(borderIdx1, borderIdx2)
        if commonBorders is None:
            return False

        # Check that all the other borders in that vertex are BLANK.
        for bdrIdx in commonBorders:
            if bdrIdx != borderIdx1 and bdrIdx != borderIdx2:
                if board.borders[bdrIdx] != BorderStatus.BLANK:
                    return False

        # If all of the above conditions are true, return True.
        return True

    def getDirectionsCellIsPokingAt(self, board: Board, row: int, col: int) \
            -> list[DiagonalDirection]:
        """
        Returns a list of corner directions where the given cell is poking at.

        Arguments:
            board: The board.
            row: The row index of the cell.
            col: The column index of the cell.
        """
        pokeDirs: set[DiagonalDirection] = set()

        reqNum = board.cells[row][col]
        borders = board.tools.getCellBorders(row, col)
        _, countActive, countBlank = self.getStatusCount(board, borders)

        if reqNum == 3 and countActive > 1:
            for dxn in DiagonalDirection:
                bdrStat1, bdrStat2 = board.getCornerStatus(row, col, dxn)
                if bdrStat1 == BorderStatus.ACTIVE and bdrStat2 == BorderStatus.ACTIVE:
                    pokeDirs.add(dxn.opposite())

        if reqNum == 1 and countBlank == 2:
            for dxn in DiagonalDirection:
                bdrStat1, bdrStat2 = board.getCornerStatus(row, col, dxn)
                if bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.UNSET:
                    pokeDirs.add(dxn)

        if reqNum == 2 and countActive == 1 and countBlank == 1:
            for dxn in DiagonalDirection:
                bdrStat1, bdrStat2 = board.getCornerStatus(row, col, dxn)
                if bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.UNSET:
                    pokeDirs.add(dxn)
                    break

        for dxn in DiagonalDirection:
            bdrStat1, bdrStat2 = board.getCornerStatus(row, col, dxn)
            if (bdrStat1 == BorderStatus.ACTIVE and bdrStat2 == BorderStatus.BLANK) or \
                    (bdrStat1 == BorderStatus.BLANK and bdrStat2 == BorderStatus.ACTIVE):
                pokeDirs.add(dxn)

        return list(pokeDirs)

    def isCellIndirectPokedByPropagation(self, board: Board, currCellIdx: tuple[int, int],
                                         dxn: DiagonalDirection) -> bool:
        """
        Check if a cell is being indirectly poked by propagation.

        Arguments:
            board: The board.
            origCellIdx: The index of the target cell.
            currCellIdx: The index of the 2-cell currently being checked.
            dxn: The propagation direction.

        Returns:
            True if a cell is being indirectly poked by propagation.
            False otherwise.
        """
        if currCellIdx is None:
            return False

        currRow, currCol = currCellIdx

        if not board.tools.isValidCellIdx(currRow, currCol):
            return False

        if board.cells[currRow][currCol] == 3:
            return True

        cornerBdrs = board.tools.getCornerBorderIndices(currRow, currCol, dxn.opposite())
        _, countActive, _ = self.getStatusCount(board, cornerBdrs)

        if countActive > 1:
            raise InvalidBoardException('Checking for INDIRECT poking, but found '
                                        f'more than one active border: {cornerBdrs}')

        if countActive == 1:
            return True

        if board.cells[currRow][currCol] != 2:
            return False

        nextCellIdx = board.tools.getCellIdxAtDiagCorner(currRow, currCol, dxn)
        return self.isCellIndirectPokedByPropagation(board, nextCellIdx, dxn)

    def getContinuousUnsetBordersOfCell(self, board: Board, cellInfo: CellInfo) -> list[list[int]]:
        """
        Returns the `UNSET` borders of a cell who are continuous with each other.

        Arguments:
            board: The board.
            cellInfo: The cell information.
        """
        result: list[list[int]] = []

        if cellInfo.bdrUnsetCount < 2:
            return []

        topBdr, rightBdr, botBdr, leftBdr = cellInfo.bdrIndices

        isTopUnset = cellInfo.topBdr == BorderStatus.UNSET
        isRightUnset = cellInfo.rightBdr == BorderStatus.UNSET
        isBotUnset = cellInfo.botBdr == BorderStatus.UNSET
        isLeftUnset = cellInfo.leftBdr == BorderStatus.UNSET

        # TOP-RIGHT-BOT
        if isTopUnset and isRightUnset and isBotUnset:
            if self.isContinuous(board, topBdr, rightBdr) and \
                    self.isContinuous(board, rightBdr, botBdr):
                return [[topBdr, rightBdr, botBdr]]

        # RIGHT-BOT-LEFT
        if isRightUnset and isBotUnset and isLeftUnset:
            if self.isContinuous(board, rightBdr, botBdr) and \
                    self.isContinuous(board, botBdr, leftBdr):
                return [[rightBdr, botBdr, leftBdr]]

        # BOT-LEFT-TOP
        if isBotUnset and isLeftUnset and isTopUnset:
            if self.isContinuous(board, botBdr, leftBdr) and \
                    self.isContinuous(board, leftBdr, topBdr):
                return [[botBdr, leftBdr, topBdr]]

        # LEFT-TOP-RIGHT
        if isLeftUnset and isTopUnset and isRightUnset:
            if self.isContinuous(board, leftBdr, topBdr) and \
                    self.isContinuous(board, topBdr, rightBdr):
                return [[leftBdr, topBdr, rightBdr]]

        # TOP-RIGHT
        if isTopUnset and isRightUnset:
            if self.isContinuous(board, topBdr, rightBdr):
                result.append([topBdr, rightBdr])

        # RIGHT-BOT
        if isRightUnset and isBotUnset:
            if self.isContinuous(board, rightBdr, botBdr):
                result.append([rightBdr, botBdr])

        # BOT-LEFT
        if isBotUnset and isLeftUnset:
            if self.isContinuous(board, botBdr, leftBdr):
                result.append([botBdr, leftBdr])

        # LEFT-TOP
        if isLeftUnset and isTopUnset:
            if self.isContinuous(board, leftBdr, topBdr):
                result.append([leftBdr, topBdr])

        return result
