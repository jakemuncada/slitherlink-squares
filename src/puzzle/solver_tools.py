"""
This module contains functions for solving the board.
"""

from src.puzzle.enums import BorderStatus, CardinalDirection, CornerEntry, DiagonalDirection

from .board import Board


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

    def getStatusCount(self, board: Board, bdrIdxList: list[int]) -> tuple[int, int, int]:
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

    def getCornerProtrusionsOfCell(self, board: Board, row: int, col: int) -> list[DiagonalDirection]:
        """
        Determine which corners of the cell a protrusion occurs.
        A protrusion is where exactly one border of that corner is `ACTIVE`.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.

        Returns:
            A list containing the corner directions where protrusions occur.
        """
        reqNum = board.cells[row][col]

        # if reqNum == 3:
        #     self.getCornerProtrusionsOf3Cell(board, row, col)
        
        if reqNum == 2:
            self.getCornerProtrusionOf2Cell(board, row, col)

    def getCornerProtrusionsOf3Cell(self, board: Board, row: int, col: int) -> list[DiagonalDirection]:
        """
        Determine which corners of the 3-cell a protrusion occurs.
        A protrusion is where exactly one border of that corner is (or will be) `ACTIVE`.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.

        Returns:
            A list containing the corner directions where protrusions occur.
        """
        # result: list[DiagonalDirection] = []

        
        # countUnset, countActive, countBlank = self.getStatusCount(board, )

        # isTopActive, isRightActive, isBotActive, isLeftActive = \
        #     self.getCellBordersBoolStatus(board, row, col, BorderStatus.ACTIVE)

        # isTopBlank, isRightBlank, isBotBlank, isLeftBlank = \
        #     self.getCellBordersBoolStatus(board, row, col, BorderStatus.BLANK)

        


    def getCornerProtrusionsOf2Cell(self, board: Board, row: int, col: int) -> list[DiagonalDirection]:
        """
        Determine which corners of the 2-cell a protrusion occurs.
        A protrusion is where exactly one border of that corner is `ACTIVE`.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.

        Returns:
            A list containing the corner directions where protrusions occur.
        """
        if board.cells[row][col] != 2:
            return []

        cornersAll = [DiagonalDirection.ULEFT, DiagonalDirection.URIGHT, DiagonalDirection.LRIGHT, DiagonalDirection.LLEFT]
        cornersULLR = [DiagonalDirection.ULEFT, DiagonalDirection.LRIGHT]
        cornersURLL = [DiagonalDirection.URIGHT, DiagonalDirection.LLEFT]

        # protrusions: set[DiagonalDirection] = set()        

        # armsUL, armsUR, armsLR, armsLL = board.tools.getArmsOfCell(row, col)
        # statUL = self.getStatusCount(board, armsUL)
        # statUR = self.getStatusCount(board, armsUR)
        # statLR = self.getStatusCount(board, armsLR)
        # statLL = self.getStatusCount(board, armsLL)
        
        # # If the UL corner has one ACTIVE and no UNSET
        # if statUL[1] == 1 and statUL[0] == 0:
        #     protrusions.add(DiagonalDirection.ULEFT)
        #     protrusions.add(DiagonalDirection.LRIGHT)
        # # If the UR corner has one ACTIVE and no UNSET
        # if statUR[1] == 1 and statUR[0] == 0:
        #     protrusions.add(DiagonalDirection.URIGHT)
        #     protrusions.add(DiagonalDirection.LLEFT)
        # # If the LR corner has one ACTIVE and no UNSET
        # if statLR[1] == 1 and statLR[0] == 0:
        #     protrusions.add(DiagonalDirection.LRIGHT)
        #     protrusions.add(DiagonalDirection.ULEFT)
        # # If the LL corner has one ACTIVE and no UNSET
        # if statLL[1] == 1 and statLL[0] == 0:
        #     protrusions.add(DiagonalDirection.LLEFT)
        #     protrusions.add(DiagonalDirection.URIGHT)
        
        # if len(protrusions) == 4:
        #     return list(protrusions)

        isTopActive, isRightActive, isBotActive, isLeftActive = \
            self.getCellBordersBoolStatus(board, row, col, BorderStatus.ACTIVE)

        isTopBlank, isRightBlank, isBotBlank, isLeftBlank = \
            self.getCellBordersBoolStatus(board, row, col, BorderStatus.BLANK)

        # If opposite borders are active
        if isTopActive and isBotActive:
            return cornersAll
        if isLeftActive and isRightActive:
            return cornersAll

        # If adjacent borders are active
        if isTopActive and isRightActive:
            return cornersULLR
        if isRightActive and isBotActive:
            return cornersURLL
        if isBotActive and isLeftActive:
            return cornersULLR
        if isLeftActive and isTopActive:
            return cornersURLL

        # If an active border is adjacent a blank border
        if isTopActive and isRightBlank:
            return cornersURLL
        if isTopActive and isLeftBlank:
            return cornersULLR
        if isRightActive and isBotBlank:
            return cornersULLR
        if isRightActive and isTopBlank:
            return cornersURLL
        if isBotActive and isLeftBlank:
            return cornersURLL
        if isBotActive and isRightBlank:
            return cornersULLR
        if isLeftActive and isTopBlank:
            return cornersULLR
        if isLeftActive and isBotBlank:
            return cornersURLL

        return []

    def getBoardCornerEntryStatus(self, board: Board) \
        -> list[list[tuple[CornerEntry, CornerEntry, CornerEntry, CornerEntry]]]:
        """
        Get the corner entry status of each cell on the board.

        Arguments:
            board: The board.

        Returns:
            A two-dimensional array containing each cell's corner entry status.
        """
        boardCornerEntryStatus = []
        for row in range(len(board.rows)):
            rowCornerEntryStatus = []
            for col in range(len(board.cols)):
                status = self.getCellCornerEntryStatus(board, row, col)
                rowCornerEntryStatus.append(status)
            boardCornerEntryStatus.append(rowCornerEntryStatus)
        return boardCornerEntryStatus

    def getCellCornerEntryStatus(self, board: Board, row: int, col: int) \
        -> tuple[CornerEntry, CornerEntry, CornerEntry, CornerEntry]:
        """
        Get the corner entry status of the target cell.

        The corner entry status is a 4-tuple representing how many "outer arms" 
        are active in the cell's corners. The tuple has the `ULEFT`, `URIGHT`,
        `LRIGHT`, and `LLEFT` statuses in that order.

        Arguments:
            board: The board.

        Returns:
            A two-dimensional array containing each cell's corner entry status.
        """
        topBdr = board.tools.getBorderIdx(row, col, CardinalDirection.TOP)
        rightBdr = board.tools.getBorderIdx(row, col, CardinalDirection.RIGHT)
        botBdr = board.tools.getBorderIdx(row, col, CardinalDirection.BOT)
        leftBdr = board.tools.getBorderIdx(row, col, CardinalDirection.LEFT)

        isTopActive = board.borders[topBdr] == BorderStatus.ACTIVE
        isRightActive = board.borders[rightBdr] == BorderStatus.ACTIVE
        isBotActive = board.borders[botBdr] == BorderStatus.ACTIVE
        isLeftActive = board.borders[leftBdr] == BorderStatus.ACTIVE

        statusUL = CornerEntry.UNKNOWN
        statusUR = CornerEntry.UNKNOWN
        statusLR = CornerEntry.UNKNOWN
        statusLL = CornerEntry.UNKNOWN

        # ULEFT
        # if (isTopActive and not isLeftActive) or (isLeftActive and not isTopActive):
        #     statusUL = CornerEntry.ONE
        # elif 

        # URIGHT
        # LRIGHT
        # LLEFT


        # contUnsetBdrs = self.getContinuousUnsetBordersOfCell(self.board, row, col)
        # if len(contUnsetBdrs) > 0:
        #     # If a 1-cell has continuous unset borders, they should be set to BLANK.
        #     if reqNum == 1:
        #         for bdrSet in contUnsetBdrs:
        #             for bdrIdx in bdrSet:
        #                 if self.setBorder(bdrIdx, BorderStatus.UNSET):
        #                     print(f'Removing continous borders of 1-cell: {cellIdx}')
        #                     foundMove = True