"""
This module contains functions for solving the board.
"""

from typing import Union

from src.puzzle.board import Board
from src.puzzle.board_tools import BoardTools
from src.puzzle.enums import BorderStatus, CardinalDirection, DiagonalDirection, InvalidBoardException, OptInt


class SolverTools:
    """
    Class containing functions to help in solving the board.
    """

    @staticmethod
    def getStatusCount(board: Board, bdrIdxList: Union[list[int], set[int], tuple]) \
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

    @staticmethod
    def isAdjCellReqNumEqualTo(board: Board, row: int, col: int,
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
        adjRow, adjCol = BoardTools.getCellIdxOfAdjCell(row, col, dxn)
        if adjRow is None or adjCol is None:
            return False
        return board.cells[adjRow][adjCol] == query

    @staticmethod
    def isContinuous(board: Board, borderIdx1: int, borderIdx2: int) -> bool:
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
        if not BoardTools.isValidBorderIdx(borderIdx1):
            return False

        if not BoardTools.isValidBorderIdx(borderIdx2):
            return False

        # The two borders should not be `BLANK`.
        if board.borders[borderIdx1] == BorderStatus.BLANK:
            return False
        if board.borders[borderIdx2] == BorderStatus.BLANK:
            return False

        # Check that the two borders are connected (share a common vertex).
        commonBorders = BoardTools.getCommonVertex(borderIdx1, borderIdx2)
        if commonBorders is None:
            return False

        # Check that all the other borders in that vertex are BLANK.
        for bdrIdx in commonBorders:
            if bdrIdx != borderIdx1 and bdrIdx != borderIdx2:
                if board.borders[bdrIdx] != BorderStatus.BLANK:
                    return False

        # If all of the above conditions are true, return True.
        return True

    @staticmethod
    def isCellIndirectPokedByPropagation(board: Board, currCellIdx: tuple[int, int],
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

        if not BoardTools.isValidCellIdx(currRow, currCol):
            return False

        if board.cells[currRow][currCol] == 3:
            return True

        cornerBdrs = BoardTools.getCornerBorderIndices(currRow, currCol, dxn.opposite())
        _, countActive, _ = SolverTools.getStatusCount(board, cornerBdrs)

        if countActive > 1:
            raise InvalidBoardException('Checking for INDIRECT poking, but found '
                                        f'more than one active border: {cornerBdrs}')

        if countActive == 1:
            return True

        if board.cells[currRow][currCol] != 2:
            return False

        nextCellIdx = BoardTools.getCellIdxAtDiagCorner(currRow, currCol, dxn)
        return SolverTools.isCellIndirectPokedByPropagation(board, nextCellIdx, dxn)
