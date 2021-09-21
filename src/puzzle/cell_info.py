"""
This module contains the CellInfo class.
"""

from __future__ import annotations

from src.puzzle.board import Board
from src.puzzle.board_tools import BoardTools
from src.puzzle.enums import BorderStatus, OptInt


class CellInfo:
    """
    Class that contains useful information of a cell.
    """
    @classmethod
    def init(cls, board: Board, row: int, col: int) -> CellInfo:
        """
        Get the cell information from the board.
        """
        info = cls(row, col)
        info.reqNum = board.cells[row][col]
        info.cellGroup = board.cellGroups[row][col]
        info.getBorderStats(board)
        return info

    def __init__(self, row: int, col: int) -> None:
        self.row = row
        self.col = col

        self.reqNum: OptInt = None
        self.cellGroup: OptInt = None

        self.bdrIndices: tuple[int, int, int, int] = (-1, -1, -1, -1)
        self.topIdx: int = -1
        self.rightIdx: int = -1
        self.botIdx: int = -1
        self.leftIdx: int = -1

        self.bdrStats: list[BorderStatus, BorderStatus, BorderStatus, BorderStatus] = []
        self.topBdr: BorderStatus = BorderStatus.UNSET
        self.rightBdr: BorderStatus = BorderStatus.UNSET
        self.botBdr: BorderStatus = BorderStatus.UNSET
        self.leftBdr: BorderStatus = BorderStatus.UNSET

        self.bdrUnsetCount: int = 4
        self.bdrActiveCount: int = 0
        self.bdrBlankCount: int = 0

        self.unsetBorders: set[int] = set()
        self.activeBorders: set[int] = set()
        self.blankBorders: set[int] = set()

        self.armsTuple: tuple[list[int], list[int], list[int], list[int]] = (None, None, None, None)
        self.armsUL: list[int] = None
        self.armsUR: list[int] = None
        self.armsLR: list[int] = None
        self.armsLL: list[int] = None

    def getBorderIndices(self, board: Board) -> tuple[int, int, int, int]:
        """
        Get the border indices and save it for future use.
        """
        if self.bdrIndices[0] != -1:
            return self.bdrIndices

        self.bdrIndices = BoardTools.getCellBorders(self.row, self.col)
        self.topIdx = self.bdrIndices[0]
        self.rightIdx = self.bdrIndices[1]
        self.botIdx = self.bdrIndices[2]
        self.leftIdx = self.bdrIndices[3]

        self.cornerUL = (self.topIdx, self.leftIdx)
        self.cornerUR = (self.topIdx, self.rightIdx)
        self.cornerLR = (self.botIdx, self.rightIdx)
        self.cornerLL = (self.botIdx, self.leftIdx)
        self.cornerBdrs = (self.cornerUL, self.cornerUR, self.cornerLR, self.cornerLL)

        return self.bdrIndices

    def getBorderStats(self, board: Board) -> tuple[BorderStatus, BorderStatus, BorderStatus, BorderStatus]:
        """
        Get the status of each border and save it for future use.
        """
        self.bdrStats = [board.borders[idx] for idx in self.getBorderIndices(board)]
        self.topBdr = self.bdrStats[0]
        self.rightBdr = self.bdrStats[1]
        self.botBdr = self.bdrStats[2]
        self.leftBdr = self.bdrStats[3]

        self.bdrUnsetCount = 0
        self.bdrActiveCount = 0
        self.bdrBlankCount = 0

        self.unsetBorders = set()
        self.activeBorders = set()
        self.blankBorders = set()

        for i in range(4):
            stat = self.bdrStats[i]
            if stat == BorderStatus.UNSET:
                self.bdrUnsetCount += 1
                self.unsetBorders.add(self.bdrIndices[i])
            elif stat == BorderStatus.ACTIVE:
                self.bdrActiveCount += 1
                self.activeBorders.add(self.bdrIndices[i])
            elif stat == BorderStatus.BLANK:
                self.bdrBlankCount += 1
                self.blankBorders.add(self.bdrIndices[i])

        return self.bdrStats

    def getArms(self, board: Board) -> tuple[list[int], list[int], list[int], list[int]]:
        """
        Get the arms at each corner direction and save it for future use.
        """
        self.armsTuple = BoardTools.getArmsOfCell(self.row, self.col)
        self.armsUL = self.armsTuple[0]
        self.armsUR = self.armsTuple[1]
        self.armsLR = self.armsTuple[2]
        self.armsLL = self.armsTuple[3]

        return self.bdrStats
