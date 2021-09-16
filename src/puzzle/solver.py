"""
Solver for Slitherlink-Squares.
"""

import time

from src.puzzle.solver_init import _setBorder, solveInit
from src.puzzle.solver_tools import SolverTools
from src.puzzle.enums import BorderStatus, CardinalDirection, CellBdrs
from .board import Board


class Solver():
    """Solver for Slitherlink-Squares"""

    def __init__(self, board: Board):
        """
        Initialize a Solver for a given board.
        """
        self.origBoard = board
        self.board = board
        self.tools = SolverTools()

        self.allCells: set[tuple[int, int]] = set()
        self.reqCells: set[tuple[int, int]] = set()
        self.unreqCells: set[tuple[int, int]] = set()

        self.cellBorders: CellBdrs = []

        for i in range(len(board.cells)):
            self.cellBorders.append([])
            for j in range(len(board.cells[i])):
                self.allCells.add((i, j))
                if board.cells[i][j] != None:
                    self.reqCells.add((i, j))
                else:
                    self.unreqCells.add((i, j))

                topBdr = board.tools.getBorderIdx(i, j, CardinalDirection.TOP)
                rightBdr = board.tools.getBorderIdx(i, j, CardinalDirection.RIGHT)
                botBdr = board.tools.getBorderIdx(i, j, CardinalDirection.BOT)
                leftBdr = board.tools.getBorderIdx(i, j, CardinalDirection.LEFT)
                self.cellBorders[i].append((topBdr, rightBdr, botBdr, leftBdr))

    def solveBoard(self) -> None:
        """
        Solve the entire board.
        """
        t0 = time.time()

        solveInit(self.board, self.reqCells, self.cellBorders)
        moveFound = True
        while moveFound:
            moveFound = self.solveObvious()
        
        print('No more moves found. Time elapsed: {:.3f} seconds.'.format(time.time() - t0))

    def _solve(self):
        """
        Solve the board. Returns the final status of the borders of the solved board.
        Returns None if the board cannot be solved in its current state.

        Important:
            Assumes that the board is valid at the point that this method is called.

        Returns:
            [BorderStatus]: An array containing the border status of the final solved board.
        """

    def setBorder(self, borderIdx: int, newStatus: BorderStatus) -> bool:
        """
        Set the specified border's status.

        Arguments:
            borderIdx: The index of the target border.
            newStatus: The new border status.

        Returns:
            True if the border was set to the new status.
            False if the border was already in that status.
        """
        if self.board.borders[borderIdx] != newStatus:
            self.board.setBorderStatus(borderIdx, newStatus)
            return True
        return False                   

    def solveObvious(self) -> bool:
        """
        Solve the obvious borders. Returns true if a move was found. Returns false otherwise.
        """
        foundMove = False
        processedBorders: set[int] = set()

        for cellIdx in self.allCells:
            row = cellIdx[0]
            col = cellIdx[1]

            if self.processCell(cellIdx):
                foundMove = True

            for dxn in CardinalDirection:
                borderIdx = self.board.tools.getBorderIdx(row, col, dxn)
                if not borderIdx in processedBorders:
                    processedBorders.add(borderIdx)
                    if self.processBorder(borderIdx):
                        foundMove = True

        return foundMove

    def processCell(self, cellIdx: tuple[int, int]) -> bool:
        """
        Checks a cell for clues.
        Returns true if a move was found. Returns false otherwise.
        """
        foundMove = False
        row = cellIdx[0]
        col = cellIdx[1]
        reqNum = self.board.cells[row][col]

        if reqNum != None:
            if self.tools.shouldFillUpRemainingUnsetBorders(self.board, row, col):
                for borderIdx in self.board.getUnsetBordersOfCell(row, col):
                    if self.setBorder(borderIdx, BorderStatus.ACTIVE):
                        print(f'Filling up: Cell {cellIdx}')
                        foundMove = True

            elif self.tools.shouldRemoveRemainingUnsetBorders(self.board, row, col):
                for borderIdx in self.board.getUnsetBordersOfCell(row, col):
                    if self.setBorder(borderIdx, BorderStatus.BLANK):
                        print(f'Removing remaining borders: Cell {cellIdx}')
                        foundMove = True

            if reqNum == 2:
                foundMove = foundMove | self.handle2CellDiagonallyOppositeActiveArms(row, col)

            if foundMove:
                return True

            contUnsetBdrs = self.tools.getContinuousUnsetBordersOfCell(self.board, row, col)

            if len(contUnsetBdrs) > 0:
                # If a 1-cell has continuous unset borders, they should be set to BLANK.
                if reqNum == 1:
                    for bdrSet in contUnsetBdrs:
                        for bdrIdx in bdrSet:
                            if self.setBorder(bdrIdx, BorderStatus.BLANK):
                                print(f'Removing continous borders of 1-cell: {cellIdx}')
                                foundMove = True
                
                # If a 3-cell has continuous unset borders, they should be set to ACTIVE.
                if reqNum == 3:
                    for bdrSet in contUnsetBdrs:
                        for bdrIdx in bdrSet:
                            if self.setBorder(bdrIdx, BorderStatus.ACTIVE):
                                print(f'Activating continuous borders of 3-cell: {cellIdx}')
                                foundMove = True

                # If a 2-cell has continuous unset borders
                # INVALID: If the continuous border has a length of 3
                if reqNum == 2:
                    # If the 2-cell has continuos UNSET borders and also has at least one BLANK border,
                    # then the continuous UNSET borders should be activated.
                    _, _, countBlank = self.tools.getStatusCount(self.board, self.cellBorders[row][col])
                    if countBlank > 0:
                        for bdrIdx in contUnsetBdrs[0]:
                            if self.setBorder(bdrIdx, BorderStatus.ACTIVE):
                                print(f'Activating continuous borders of 2-cell: {cellIdx}')
                                foundMove = True
        
        return foundMove

    def processBorder(self, borderIdx: int) -> bool:
        """
        Check a border for clues. Returns true if a move was found.
        Returns false otherwise.
        """
        foundMove = False
        if self.board.borders[borderIdx] == BorderStatus.UNSET:

            connBdrList = self.board.tools.getConnectedBordersList(borderIdx)
            for connBdrIdx in connBdrList:
                if self.tools.isContinuous(self.board, borderIdx, connBdrIdx):
                    if self.board.borders[connBdrIdx] == BorderStatus.ACTIVE:
                        if self.setBorder(borderIdx, BorderStatus.ACTIVE):
                            print(f'Activating continuous line: {borderIdx} to {connBdrIdx}')
                            return True

            connBdrTuple = self.board.tools.getConnectedBorders(borderIdx)

            _, countActive1, countBlank1 = self.tools.getStatusCount(self.board, connBdrTuple[0])
            _, countActive2, countBlank2 = self.tools.getStatusCount(self.board, connBdrTuple[1])

            if countActive1 > 1 or countActive2 > 1:
                if self.setBorder(borderIdx, BorderStatus.BLANK):
                    print(f'Cleaning up active corner: {borderIdx}')
                    return True

            if countBlank1 == len(connBdrTuple[0]) or countBlank2 == len(connBdrTuple[1]):
                if self.setBorder(borderIdx, BorderStatus.BLANK):
                    print(f'Cleaning up hanging border: {borderIdx}')
                    return True

        return foundMove

    def handle2CellDiagonallyOppositeActiveArms(self, row: int, col: int) -> bool:
        """
        Handle the case when a 2-cell has active arms in opposite corners.
        Returns true if a move was found. Returns false otherwise.
        """
        if self.board.cells[row][col] != 2:
            return False

        foundMove = False
        armsUL, armsUR, armsLR, armsLL = self.board.tools.getArmsOfCell(row, col)

        # INVALID: If one corner has 2 active arms and the opposite corner has at least 1 active arm.

        _, activeCount1, _ = self.tools.getStatusCount(self.board, armsUL)
        _, activeCount2, _ = self.tools.getStatusCount(self.board, armsLR)
        if activeCount1 == 1 and activeCount2 == 1:
            for bdrIdx in armsUL + armsLR:
                if self.board.borders[bdrIdx] == BorderStatus.UNSET:
                    self.setBorder(bdrIdx, BorderStatus.BLANK)
                    foundMove = True
        
        _, activeCount1, _ = self.tools.getStatusCount(self.board, armsUR)
        _, activeCount2, _ = self.tools.getStatusCount(self.board, armsLL)
        if activeCount1 == 1 and activeCount2 == 1:
            for bdrIdx in armsUR + armsLL:
                if self.board.borders[bdrIdx] == BorderStatus.UNSET:
                    self.setBorder(bdrIdx, BorderStatus.BLANK)
                    foundMove = True
        
        return foundMove
