"""
This module contains functions for solving the board.
"""

from typing import Union

from .board import Board
from src.puzzle.enums import BorderStatus, CardinalDirection, DiagonalDirection


class SolverTools:
    """
    Class containing functions to help in solving the board.
    """

    def __init__(self) -> None:
        pass

    def isCellDone(self, board: Board, row: int, col: int) -> bool:
        """
        Returns true if there are no more remanining `UNSET` borders in the target cell.
        Returns false otherwise.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.
        """
        for direction in CardinalDirection:
            status = board.getBorderStatus(row, col, direction)
            if status == BorderStatus.UNSET:
                return False
        return True

    def getCellBordersBoolStatus(self, board: Board, row: int, col: int, status: BorderStatus) \
            -> tuple[bool, bool, bool, bool]:
        """
        Determine if the status of the four cell borders are equal to the given BorderStatus.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.
            status: The query status.

        Returns:
            A 4-tuple of boolean values corresponding to the four border directions:
            `TOP`, `RIGHT`, `BOT`, and `LEFT`.
        """
        bdrIdxTop = board.tools.getBorderIdx(row, col, CardinalDirection.TOP)
        bdrIdxRight = board.tools.getBorderIdx(row, col, CardinalDirection.RIGHT)
        bdrIdxBot = board.tools.getBorderIdx(row, col, CardinalDirection.BOT)
        bdrIdxLeft = board.tools.getBorderIdx(row, col, CardinalDirection.LEFT)

        topStatus = board.borders[bdrIdxTop] == status
        rightStatus = board.borders[bdrIdxRight] == status
        botStatus = board.borders[bdrIdxBot] == status
        leftStatus = board.borders[bdrIdxLeft] == status

        return (topStatus, rightStatus, botStatus, leftStatus)

    def getStatusCount(self, board: Board, bdrIdxList: Union[list[int], set[int], tuple]) -> tuple[int, int, int]:
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
            if board.tools.isValidBorderIdx(idx):
                if board.borders[idx] == BorderStatus.UNSET:
                    countUnset += 1
                elif board.borders[idx] == BorderStatus.ACTIVE:
                    countActive += 1
                elif board.borders[idx] == BorderStatus.BLANK:
                    countBlank += 1
        return (countUnset, countActive, countBlank)

    def countUnset(self, board: Board, bdrIdxList: list[int]) -> int:
        """
        Returns the number of `UNSET` borders in the given list.
        """
        count = 0
        for idx in bdrIdxList:
            if board.tools.isValidBorderIdx(idx):
                if board.borders[idx] == BorderStatus.UNSET:
                    count += 1
        return count

    def countActive(self, board: Board, bdrIdxList: list[int]) -> int:
        """
        Returns the number of `ACTIVE` borders in the given list.
        """
        count = 0
        for idx in bdrIdxList:
            if board.tools.isValidBorderIdx(idx):
                if board.borders[idx] == BorderStatus.ACTIVE:
                    count += 1
        return count

    def countBlank(self, board: Board, bdrIdxList: list[int]) -> int:
        """
        Returns the number of `BLANK` borders in the given list.
        """
        count = 0
        for idx in bdrIdxList:
            if board.tools.isValidBorderIdx(idx):
                if board.borders[idx] == BorderStatus.BLANK:
                    count += 1
        return count

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

    def shouldFillUpRemainingUnsetBorders(self, board: Board, row: int, col: int) -> bool:
        """
        Returns true if all the remaining `UNSET` borders of the target cell 
        should be set to `ACTIVE`. Returns false otherwise.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.
        """
        num = board.cells[row][col]
        if num is not None:
            count = 0
            for direction in CardinalDirection:
                status = board.getBorderStatus(row, col, direction)
                if status != BorderStatus.BLANK:
                    count += 1
            if count == num:
                return True
        return False

    def shouldRemoveRemainingUnsetBorders(self, board: Board, row: int, col: int) -> bool:
        """
        Returns true if all the remaining `UNSET` borders of the target cell 
        should be set to `BLANK`. Returns false otherwise.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.
        """
        num = board.cells[row][col]
        if num is not None:
            count = 0
            for direction in CardinalDirection:
                status = board.getBorderStatus(row, col, direction)
                if status == BorderStatus.ACTIVE:
                    count += 1
            if count == num:
                return True
        return False

    def getDirectionsCellIsPokingAt(self, board: Board, row: int, col: int) -> list[DiagonalDirection]:
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

    def getDirectionsCellIsBeingExplicitlyPokedFrom(self, board: Board, row: int, col: int) -> list[DiagonalDirection]:
        """
        Returns a list of corner directions where the given cell is being explicitly poked from.

        An 'explicit poke' is when exactly one arm from the given direction is `ACTIVE`
        and the rest are `BLANK`.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.
        """
        pokeDirs: list[DiagonalDirection] = []
        for dxn in DiagonalDirection:
            if self.isCellExplicitlyPoked(board, row, col, dxn):
                pokeDirs.append(dxn)
        return pokeDirs

    def isCellExplicitlyPoked(self, board: Board, row: int, col: int, dxn: DiagonalDirection) -> bool:
        """
        Returns true if the cell is being explicitly poked from a specific direction.

        An 'explicit poke' is when exactly one arm from the given direction is `ACTIVE`
        and the rest are `BLANK`.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.
            dxn: The specified direction.
        """
        arms = board.tools.getArms(row, col, dxn)
        countUnset, countActive, _ = self.getStatusCount(board, arms)
        return countActive == 1 and countUnset == 0

    def getContinuousUnsetBordersOfCell(self, board: Board, row: int, col: int) -> list[list[int]]:
        """
        Returns the `UNSET` borders of a cell who are continuous with each other.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.
        """
        result: list[list[int]] = []

        topBdr = board.tools.getBorderIdx(row, col, CardinalDirection.TOP)
        rightBdr = board.tools.getBorderIdx(row, col, CardinalDirection.RIGHT)
        botBdr = board.tools.getBorderIdx(row, col, CardinalDirection.BOT)
        leftBdr = board.tools.getBorderIdx(row, col, CardinalDirection.LEFT)

        isTopUnset = board.borders[topBdr] == BorderStatus.UNSET
        isRightUnset = board.borders[rightBdr] == BorderStatus.UNSET
        isBotUnset = board.borders[botBdr] == BorderStatus.UNSET
        isLeftUnset = board.borders[leftBdr] == BorderStatus.UNSET

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
