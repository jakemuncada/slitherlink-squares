"""
Solver for Slitherlink-Squares.
"""

import time
import random
from functools import cache
from typing import Optional, Callable

from src.puzzle.board import Board
from src.puzzle.cell_info import CellInfo
from src.puzzle.board_tools import BoardTools
from src.puzzle.solver.tools import SolverTools
from src.puzzle.solver.initial import solveInit
from src.puzzle.enums import BorderStatus, CardinalDirection, \
    CornerEntry, DiagonalDirection, InvalidBoardException


class Solver():
    """Solver for Slitherlink-Squares"""

    def __init__(self, board: Board):
        """
        Initialize a Solver for a given board.
        """
        self.rows = board.rows
        self.cols = board.cols
        self.board = board
        self.tools = SolverTools()
        self.initialized = False
        self.cornerEntry: list[list[list[CornerEntry]]]
        self.prioCells: list[tuple[int, int]] = []
        self.initializePrioritizedCellList()

    def initializePrioritizedCellList(self) -> None:
        """
        Initialize the list of cells ranked in order of priority.
        """
        highPrio: list[tuple[int, int]] = []
        medPrio: list[tuple[int, int]] = []
        lowPrio: list[tuple[int, int]] = []

        for row in range(self.board.rows):
            for col in range(self.board.cols):
                reqNum = self.board.cells[row][col]
                if reqNum == 1 or reqNum == 3:
                    highPrio.append((row, col))
                elif reqNum == 2:
                    medPrio.append((row, col))
                elif reqNum is None or reqNum == 0:
                    lowPrio.append((row, col))

        self.prioCells = []
        self.prioCells.extend(highPrio)
        self.prioCells.extend(medPrio)
        self.prioCells.extend(lowPrio)

    @staticmethod
    def setBorder(board: Board, borderIdx: int, newStatus: BorderStatus) -> bool:
        """
        Set the specified border's status.

        Arguments:
            board: The board.
            borderIdx: The index of the target border.
            newStatus: The new border status.

        Returns:
            True if the border was set to the new status.
            False if the border was already in that status.
        """
        if board.borders[borderIdx] == BorderStatus.UNSET:
            board.borders[borderIdx] = newStatus
            return True
        elif board.borders[borderIdx] != newStatus:
            raise InvalidBoardException
        return False

    def solveBoardFromScratch(self, updateUI: Callable) -> None:
        """
        Solve board from scratch.
        """
        self.board.reset()
        self.cornerEntry = [[[CornerEntry.UNKNOWN, CornerEntry.UNKNOWN, CornerEntry.UNKNOWN,
                              CornerEntry.UNKNOWN, ] for _ in range(self.cols)] for _ in range(self.rows)]

        t0 = time.time()

        solveInit(self.board)
        self.initialized = True

        if updateUI:
            updateUI()

        isValid, timeElapsed = self._solve(self.board, updateUI)
        print('Initial solve: {:.3f} seconds'.format(timeElapsed))

        assert isValid, '##### ERROR: The first solve unexpectedly ' \
            'resulted in an invalid board. #####'

        currGuessIdx = 0
        guessList = self.getGuesses()
        print(f'Number of guesses found after initial solve: {len(guessList)}')

        currGuessNum = 1
        correctGuessCount = 0

        # Continue guessing until the board is completed.
        while True:
            t1 = time.time()

            if updateUI:
                updateUI()

            if currGuessIdx >= len(guessList):
                currGuessIdx = 0
                guessList = self.getGuesses()
                print(f'Number of guesses found for Guess #{currGuessNum}: {len(guessList)}')

            while currGuessIdx < len(guessList):
                guessBdrIdx, guessStatus = guessList[currGuessIdx]

                if self.board.borders[guessBdrIdx] == BorderStatus.UNSET:
                    cloneBoard = self.board.clone()
                    Solver.setBorder(cloneBoard, guessBdrIdx, guessStatus)
                    currGuessNum += 1

                    isValid, timeElapsed = self._solve(cloneBoard, updateUI)

                    # isValid = isValid and self.simpleValidation(cloneBoard)

                    # If the guess was invalid, then the opposite move should be valid.
                    if not isValid:
                        print('Guess #{}: border {} to {} [{:.3f} seconds]'.format(
                            currGuessNum, guessBdrIdx, guessStatus.opposite(), time.time() - t1))
                        Solver.setBorder(self.board, guessBdrIdx, guessStatus.opposite())
                        correctGuessCount += 1
                        break

                currGuessIdx += 1

            isValid, timeElapsed = self._solve(self.board, updateUI)
            print('Solve: {:.3f} seconds'.format(timeElapsed))

            if self.board.isComplete:
                break

        print('##################################################')
        print('Solving the board from scratch took {:.3f} seconds '
              'with {} guesses, {} of which were correct.'
              .format(time.time() - t0, currGuessNum, correctGuessCount))
        print('##################################################')

    def getGuesses(self) -> list[tuple[int, BorderStatus]]:
        """
        Get a list of moves to guess.
        """
        doneBorders: set[int] = set()
        highPrio: list[tuple[int, BorderStatus]] = []
        lowPrio: list[tuple[int, BorderStatus]] = []

        for row in range(self.board.rows):
            for col in range(self.board.cols):
                for dxn in CardinalDirection:
                    bdrIdx = BoardTools.getBorderIdx(row, col, dxn)
                    if self.board.borders[bdrIdx] == BorderStatus.UNSET:
                        doneBorders.add(bdrIdx)
                        if self.board.cells[row][col] == 1:
                            highPrio.append((bdrIdx, BorderStatus.ACTIVE))
                        elif self.board.cells[row][col] == 3:
                            highPrio.append((bdrIdx, BorderStatus.BLANK))

        for bdrIdx in range(len(self.board.borders)):
            if bdrIdx not in doneBorders:
                if self.board.borders[bdrIdx] == BorderStatus.UNSET:
                    lowPrio.append((bdrIdx, BorderStatus.ACTIVE))

        random.shuffle(highPrio)
        random.shuffle(lowPrio)

        if len(highPrio) + len(lowPrio) == 0:
            if self.board.isComplete:
                return []
            raise AssertionError('The board is not yet complete, but no guesses were found.')

        return highPrio + lowPrio

    def solveCurrentBoard(self, updateUI: Callable) -> None:
        """
        Solve the board starting from its current state.
        """
        self.cornerEntry = [[[CornerEntry.UNKNOWN, CornerEntry.UNKNOWN, CornerEntry.UNKNOWN,
                              CornerEntry.UNKNOWN, ] for _ in range(self.cols)] for _ in range(self.rows)]

        if not self.initialized:
            solveInit(self.board)
            self.initialized = True
            if updateUI:
                updateUI()

        isValid, timeElapsed = self._solve(self.board, updateUI)
        print('##################################################')
        print('Solve Current Board: {:.3f} seconds [IsValid: {}]'.format(timeElapsed, isValid))
        print('Still has {} guesses afterwards.'.format(len(self.getGuesses())))
        print('##################################################')

    def _solve(self, board: Board, updateUI: Callable = None) -> tuple[bool, float]:
        """
        Try to solve the given board. Possibly might not completely solve the board.

        Arguments:
            board: The board to solve.
            updateUI: The function to render the board onto the screen.

        Returns:
            A tuple. The first value is the board validity after solving.
            The second value is the solving duration.

            The board validity is false if an InvalidBoardException was caught while solving.
            True otherwise. Note that a return value of True does not mean
            that the board is necessarily valid.
        """
        t0 = time.time()

        try:
            moveFound = True
            while moveFound:
                moveFound = self.solveObvious(board)
                if not moveFound:
                    self.updateCellGroups(board)
                    moveFound = self.checkCellGroupClues(board)
                if not moveFound:
                    moveFound = self.removeLoopMakingMove(board)
                if not moveFound:
                    if not board.isClone:
                        moveFound = self.solveUsingCornerEntryInfo()

                if updateUI:
                    updateUI()

        except InvalidBoardException:
            return (False, time.time() - t0)

        return (True, time.time() - t0)

    def solveObvious(self, board: Board) -> bool:
        """
        Solve the obvious borders. Returns true if a move was found. Returns false otherwise.
        """
        foundMove = False
        processedBorders: set[int] = set()

        for cellIdx in self.prioCells:
            row, col = cellIdx
            if self.processCell(board, row, col):
                foundMove = True

            for dxn in CardinalDirection:
                borderIdx = BoardTools.getBorderIdx(row, col, dxn)
                if not borderIdx in processedBorders:
                    processedBorders.add(borderIdx)
                    if self.processBorder(board, borderIdx):
                        foundMove = True

        return foundMove

    def simpleValidation(self, board: Board) -> bool:
        """
        Validates the given board. The check is non-exhaustive and
        only checks obviously invalid indications.

        Arguments:
            board: The board to validate.

        Returns:
            True if the board passed the simple validation. False otherwise.
        """
        for (row, col) in board.reqCells:
            cellInfo = CellInfo.init(board, row, col)

            # If the active borders exceeded the requirement.
            if cellInfo.bdrActiveCount > cellInfo.reqNum:
                return False

            # If the active + unset borders cannot meet the requirement.
            if cellInfo.bdrActiveCount + cellInfo.bdrUnsetCount < cellInfo.reqNum:
                return False

        for bdrIdx in range(len(board.borders)):
            bdrStat = board.borders[bdrIdx]

            if bdrStat == BorderStatus.ACTIVE:
                conn = BoardTools.getConnectedBorders(bdrIdx)

                _, conn0Active, conn0Blank = self.tools.getStatusCount(board, conn[0])
                _, conn1Active, conn1Blank = self.tools.getStatusCount(board, conn[1])

                if conn0Blank == len(conn[0]):
                    return False
                if conn1Blank == len(conn[1]):
                    return False

                if conn0Active > 1:
                    return False
                if conn1Active > 1:
                    return False

        return True

    def updateCellGroups(self, board: Board) -> None:
        """
        Update the cell islands information of the board.
        """
        processedCells: set[tuple[int, int]] = set()

        def _process(row: int, col: int, groupId: int):
            if (row, col) in processedCells:
                return

            if not BoardTools.isValidCellIdx(row, col):
                return

            processedCells.add((row, col))
            board.cellGroups[row][col] = groupId

            for dxn in CardinalDirection:
                bdrStat = board.getBorderStatus(row, col, dxn)
                adjRow, adjCol = BoardTools.getCellIdxOfAdjCell(row, col, dxn)
                if adjRow is not None and adjCol is not None:
                    if bdrStat == BorderStatus.BLANK:
                        _process(adjRow, adjCol, groupId)
                    elif bdrStat == BorderStatus.ACTIVE:
                        _process(adjRow, adjCol, 1 if groupId == 0 else 0)

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

    def checkCellGroupClues(self, board: Board) -> bool:
        """
        If the cell group ID of two adjacent cells are not equal,
        the border between them should be set to `ACTIVE`.
        If the cell group ID's are equal, the border should be set to `BLANK`.
        """
        foundMove = False
        def fromAdj(isAdjEqual): return BorderStatus.BLANK if isAdjEqual else BorderStatus.ACTIVE

        for row, col in self.prioCells:
            cellInfo = CellInfo.init(board, row, col)

            borderIndices = BoardTools.getCellBorders(row, col)
            countUnset, _, _ = self.tools.getStatusCount(board, borderIndices)

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
            if cellInfo.reqNum == 1:
                if grpTop == grpBot and grpTop is not None and grpBot is not None:
                    _found = _found | Solver.setBorder(board, cellInfo.topIdx, BorderStatus.BLANK)
                    _found = _found | Solver.setBorder(board, cellInfo.botIdx, BorderStatus.BLANK)
                elif grpTop != grpBot and grpTop is not None and grpBot is not None:
                    _found = _found | Solver.setBorder(board, cellInfo.leftIdx, BorderStatus.BLANK)
                    _found = _found | Solver.setBorder(board, cellInfo.rightIdx, BorderStatus.BLANK)

                if grpLeft == grpRight and grpLeft is not None and grpRight is not None:
                    _found = _found | Solver.setBorder(board, cellInfo.leftIdx, BorderStatus.BLANK)
                    _found = _found | Solver.setBorder(board, cellInfo.rightIdx, BorderStatus.BLANK)
                elif grpLeft != grpRight and grpLeft is not None and grpRight is not None:
                    _found = _found | Solver.setBorder(board, cellInfo.topIdx, BorderStatus.BLANK)
                    _found = _found | Solver.setBorder(board, cellInfo.botIdx, BorderStatus.BLANK)

            elif cellInfo.reqNum == 2:
                if (grpTop == grpBot and grpTop is not None) or \
                        (grpLeft == grpRight and grpLeft is not None):
                    for dxn in DiagonalDirection:
                        _found = _found | self.initiatePoke(board, row, col, dxn)

            elif cellInfo.reqNum == 3:
                if grpTop == grpBot and grpTop is not None:
                    _found = _found | Solver.setBorder(board, cellInfo.topIdx, BorderStatus.ACTIVE)
                    _found = _found | Solver.setBorder(board, cellInfo.botIdx, BorderStatus.ACTIVE)
                if grpLeft == grpRight and grpLeft is not None:
                    _found = _found | Solver.setBorder(board, cellInfo.leftIdx, BorderStatus.ACTIVE)
                    _found = _found | Solver.setBorder(board, cellInfo.rightIdx, BorderStatus.ACTIVE)
                if grpTop is not None and grpBot is not None and grpTop != grpBot:
                    _found = _found | Solver.setBorder(board, cellInfo.leftIdx, BorderStatus.ACTIVE)
                    _found = _found | Solver.setBorder(board, cellInfo.rightIdx, BorderStatus.ACTIVE)
                if grpLeft is not None and grpRight is not None and grpLeft != grpRight:
                    _found = _found | Solver.setBorder(board, cellInfo.topIdx, BorderStatus.ACTIVE)
                    _found = _found | Solver.setBorder(board, cellInfo.botIdx, BorderStatus.ACTIVE)

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
                            foundMove = foundMove | self.handleSmoothCorner(board, cellInfo, dxn)
                        else:
                            foundMove = foundMove | self.initiatePoke(board, row, col, dxn)

        return foundMove

    def removeLoopMakingMove(self, board: Board) -> bool:
        """
        Find an `UNSET` border that, if set to `ACTIVE`, will create a loop.
        Since loops are prohibited, this border should be set to `BLANK`.

        Arguments:
            board: The board.

        Returns:
            True if such a border was removed. False otherwise.
        """
        t0 = time.time()

        # Get all active and unset borders
        activeBorders: set[int] = set()
        unsetBorders: set[int] = set()
        for bdrIdx in range(len(board.borders)):
            if board.borders[bdrIdx] == BorderStatus.ACTIVE:
                activeBorders.add(bdrIdx)
            elif board.borders[bdrIdx] == BorderStatus.UNSET:
                unsetBorders.add(bdrIdx)

        processedBorders: set[BorderStatus] = set()
        borderGroup: dict[int, int] = {}

        # Set all connected active borders to the same group ID
        def _process(idx: int, groupId: int) -> None:
            if idx in processedBorders:
                return
            processedBorders.add(idx)
            borderGroup[idx] = groupId
            connList = BoardTools.getConnectedBordersList(idx)
            for connBdr in connList:
                if connBdr in activeBorders:
                    _process(connBdr, groupId)

        currId = 0
        for bdrIdx in activeBorders:
            if bdrIdx in processedBorders:
                continue
            _process(bdrIdx, currId)
            currId += 1

        moveFound = False
        for bdrIdx in unsetBorders:
            conn = BoardTools.getConnectedBorders(bdrIdx)
            group1 = None
            group2 = None
            for connBdr in conn[0]:
                if connBdr in processedBorders:
                    group1 = borderGroup[connBdr]
                    break
            for connBdr in conn[1]:
                if connBdr in processedBorders:
                    group2 = borderGroup[connBdr]
                    break

            if group1 is not None and group2 is not None and group1 == group2:
                if Solver.setBorder(board, bdrIdx, BorderStatus.BLANK):
                    return True

        return moveFound

    def processCell(self, board: Board, row: int, col: int) -> bool:
        """
        Checks a cell for clues.

        Arguments:
            board: The board.
            row: The row index of the cell.
            col: The column index of the cell.

        Returns:
            True if a move was found. False otherwise.
        """
        foundMove = False

        cellInfo = CellInfo.init(board, row, col)
        reqNum = board.cells[row][col]

        if cellInfo.bdrActiveCount == 4:
            raise InvalidBoardException(f'Cell {row},{col} has 4 active borders.')

        #######################################################################
        # NOTE: For some reason, if the solver-rule below is activated,
        #       the solving time becomes worse.
        #
        # if cellInfo.bdrActiveCount == 3 and cellInfo.bdrUnsetCount == 1:
        #     for bdrIdx in cellInfo.unsetBorders:
        #         Solver.setBorder(board, bdrIdx, BorderStatus.BLANK)
        #         return True
        #######################################################################

        if reqNum is not None:

            if cellInfo.bdrActiveCount > reqNum:
                raise InvalidBoardException(f'Cell {row},{col} has {cellInfo.bdrActiveCount} '
                                            f'active borders but requires only {reqNum}.')

            if cellInfo.bdrUnsetCount + cellInfo.bdrActiveCount < reqNum:
                raise InvalidBoardException(f'Cell {row},{col} only has {cellInfo.bdrUnsetCount} '
                                            'unset borders which is not enough to get to '
                                            f'the {reqNum} requirement.')

            if self.fillOrRemoveRemainingUnsetBorders(board, cellInfo):
                return True

            if reqNum == 3:
                # If the 3-cell has an active arm, poke it.
                for dxn in DiagonalDirection:
                    armsStatus = board.getArmsStatus(row, col, dxn)
                    if any(status == BorderStatus.ACTIVE for status in armsStatus):
                        foundMove = foundMove | self.handleCellPoke(board, row, col, dxn)

                foundMove = foundMove | self.checkThreeTwoThreeTwoPattern(board, cellInfo)

            elif reqNum == 2:
                foundMove = foundMove | self.handle2CellDiagonallyOppositeActiveArms(board, row, col)

        if foundMove:
            return True

        if self.check3CellRectanglePattern(board, cellInfo):
            return True

        if self.checkOuterCellPoking(board, cellInfo):
            return True

        if not foundMove and reqNum == 3 and cellInfo.bdrUnsetCount > 0:
            # Check if the 3-cell was indirectly poked by a 2-cell (poke by propagation).
            for dxn in DiagonalDirection:
                bdrStat1, bdrStat2 = board.getCornerStatus(row, col, dxn.opposite())
                if bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.UNSET:
                    currCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
                    if self.tools.isCellIndirectPokedByPropagation(board, currCellIdx, dxn):
                        bdrIdx1, bdrIdx2 = BoardTools.getCornerBorderIndices(row, col, dxn.opposite())
                        Solver.setBorder(board, bdrIdx1, BorderStatus.ACTIVE)
                        Solver.setBorder(board, bdrIdx2, BorderStatus.ACTIVE)
                        foundMove = True

        if not foundMove and reqNum == 2 and cellInfo.bdrBlankCount == 1 and cellInfo.bdrUnsetCount > 0:
            for dxn in DiagonalDirection:
                bdrStat1, bdrStat2 = board.getCornerStatus(row, col, dxn.opposite())
                if (bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.BLANK) or \
                        (bdrStat1 == BorderStatus.BLANK and bdrStat2 == BorderStatus.UNSET):
                    currCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
                    if self.tools.isCellIndirectPokedByPropagation(board, currCellIdx, dxn):
                        if self.handleCellPoke(board, row, col, dxn):
                            return True

        # Check every cell if it is poking a diagonally adjacent cell.
        if not foundMove:
            pokeDirs = self.tools.getDirectionsCellIsPokingAt(board, row, col)
            for pokeDxn in pokeDirs:
                foundMove = foundMove | self.initiatePoke(board, row, col, pokeDxn)

        if not foundMove:
            foundMove = self.checkCellForContinuousUnsetBorders(board, cellInfo)

        return foundMove

    def fillOrRemoveRemainingUnsetBorders(self, board: Board, cellInfo: CellInfo) -> bool:
        """
        Finish off cells whose remaning `UNSET` borders could be removed or activated.
        """
        foundMove = False

        # Check if the cell has a requirement and there are still remaining unset borders.
        if cellInfo.reqNum is not None and cellInfo.bdrUnsetCount > 0:

            # If the remaining unset borders should be filled up.
            if cellInfo.bdrUnsetCount + cellInfo.bdrActiveCount == cellInfo.reqNum:
                for bdrIdx in cellInfo.unsetBorders:
                    Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE)
                    foundMove = True

            # If the required number has been met
            # and the remaining unset borders should be removed.
            elif cellInfo.bdrActiveCount == cellInfo.reqNum:
                for bdrIdx in cellInfo.unsetBorders:
                    Solver.setBorder(board, bdrIdx, BorderStatus.BLANK)
                    foundMove = True

        return foundMove

    def checkThreeTwoThreeTwoPattern(self, board: Board, cellInfo: CellInfo) -> bool:
        """
        Check and handle the case where the two 3-cells and two 2-cells
        are adjacent each other, forming a 2x2 square.

        Arguments:
            board: The board.
            row: The row index of the 3-cell.
            col: The column index of the 3-cell.

        Returns:
            True if a move was found. False otherwise.
        """
        rows = board.rows
        cols = board.cols
        row = cellInfo.row
        col = cellInfo.col
        found = False

        if row + 1 < rows and col + 1 < cols and board.cells[row + 1][col + 1] == 3:
            if board.cells[row][col + 1] == 2 and board.cells[row + 1][col] == 2:
                found = found | self.initiatePoke(board, row, col + 1, DiagonalDirection.URIGHT)
                found = found | self.initiatePoke(board, row + 1, col, DiagonalDirection.LLEFT)

        elif row + 1 < rows and col - 1 >= 0 and board.cells[row + 1][col - 1] == 3:
            if board.cells[row][col - 1] == 2 and board.cells[row + 1][col] == 2:
                found = found | self.initiatePoke(board, row, col - 1, DiagonalDirection.URIGHT)
                found = found | self.initiatePoke(board, row + 1, col, DiagonalDirection.LLEFT)

        return found

    def check3CellRectanglePattern(self, board: Board, cellInfo: CellInfo) -> bool:
        """
        Check for the special pattern where an empty cell
        with an active corner is touching a 3-cell, almost making a mini rectangle.

        Arguments:
            board: The board.
            cellInfo: The cell information.

        Returns:
            True if a move was found. False otherwise.
        """
        if cellInfo.reqNum is not None:
            return False

        if not (cellInfo.bdrActiveCount == 2 and cellInfo.bdrUnsetCount == 2):
            return False

        row = cellInfo.row
        col = cellInfo.col

        isTop3Cell = self.tools.isAdjCellReqNumEqualTo(board, row, col, CardinalDirection.TOP, 3)
        isRight3Cell = self.tools.isAdjCellReqNumEqualTo(board, row, col, CardinalDirection.RIGHT, 3)
        isBot3Cell = self.tools.isAdjCellReqNumEqualTo(board, row, col, CardinalDirection.BOT, 3)
        isLeft3Cell = self.tools.isAdjCellReqNumEqualTo(board, row, col, CardinalDirection.LEFT, 3)

        if all(board.borders[bdrIdx] == BorderStatus.ACTIVE for bdrIdx in cellInfo.cornerUL):
            if isBot3Cell:
                Solver.setBorder(board, cellInfo.rightIdx, BorderStatus.BLANK)
                return True
            if isRight3Cell:
                Solver.setBorder(board, cellInfo.botIdx, BorderStatus.BLANK)
                return True

        elif all(board.borders[bdrIdx] == BorderStatus.ACTIVE for bdrIdx in cellInfo.cornerUR):
            if isBot3Cell:
                Solver.setBorder(board, cellInfo.leftIdx, BorderStatus.BLANK)
                return True
            if isLeft3Cell:
                Solver.setBorder(board, cellInfo.botIdx, BorderStatus.BLANK)
                return True

        elif all(board.borders[bdrIdx] == BorderStatus.ACTIVE for bdrIdx in cellInfo.cornerLR):
            if isLeft3Cell:
                Solver.setBorder(board, cellInfo.topIdx, BorderStatus.BLANK)
                return True
            if isTop3Cell:
                Solver.setBorder(board, cellInfo.leftIdx, BorderStatus.BLANK)
                return True

        elif all(board.borders[bdrIdx] == BorderStatus.ACTIVE for bdrIdx in cellInfo.cornerLL):
            if isRight3Cell:
                Solver.setBorder(board, cellInfo.topIdx, BorderStatus.BLANK)
                return True
            if isTop3Cell:
                Solver.setBorder(board, cellInfo.rightIdx, BorderStatus.BLANK)
                return True

        return False

    def checkOuterCellPoking(self, board: Board, cellInfo: CellInfo) -> bool:
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
                foundMove = foundMove | self.handleCellPoke(board, row, col - 1, DiagonalDirection.URIGHT)
            if col < self.cols - 1:
                foundMove = foundMove | self.handleCellPoke(board, row, col + 1, DiagonalDirection.ULEFT)

        # If the cell is a leftmost cell, check if its LEFT border is active.
        if col == 0 and cellInfo.leftBdr == BorderStatus.ACTIVE:
            if row > 0:
                foundMove = foundMove | self.handleCellPoke(board, row - 1, col, DiagonalDirection.LLEFT)
            if row < self.rows - 1:
                foundMove = foundMove | self.handleCellPoke(board, row + 1, col, DiagonalDirection.ULEFT)

        # If the cell is a rightmost cell, check if its RIGHT border is active.
        if col == self.cols - 1 and cellInfo.rightBdr == BorderStatus.ACTIVE:
            if row > 0:
                foundMove = foundMove | self.handleCellPoke(board, row - 1, col, DiagonalDirection.LRIGHT)
            if row < self.rows - 1:
                foundMove = foundMove | self.handleCellPoke(board, row + 1, col, DiagonalDirection.URIGHT)

        # If the cell is a bottommost cell, check if its BOT border is active.
        if row == self.rows - 1 and cellInfo.botBdr == BorderStatus.ACTIVE:
            if col > 0:
                foundMove = foundMove | self.handleCellPoke(board, row, col - 1, DiagonalDirection.LRIGHT)
            if col < self.cols - 1:
                foundMove = foundMove | self.handleCellPoke(board, row, col + 1, DiagonalDirection.LLEFT)

        return foundMove

    def checkCellForContinuousUnsetBorders(self, board: Board, cellInfo: CellInfo) -> bool:
        """
        Check the borders of the cell if it has continuous unset borders.

        Arguments:
            board: The board.
            cellInfo: The cell information.

        Returns:
            True if a move was found. False otherwise.
        """
        foundMove = False
        row = cellInfo.row
        col = cellInfo.col

        if cellInfo.bdrUnsetCount < 2:
            return False

        if cellInfo.reqNum is None:
            return False

        contUnsetBdrs = self.tools.getContinuousUnsetBordersOfCell(board, cellInfo)

        if len(contUnsetBdrs) == 0:
            return False

        # If a 1-cell has continuous unset borders, they should be set to BLANK.
        if cellInfo.reqNum == 1:
            for bdrSet in contUnsetBdrs:
                for bdrIdx in bdrSet:
                    Solver.setBorder(board, bdrIdx, BorderStatus.BLANK)
                    foundMove = True

        # If a 3-cell has continuous unset borders, they should be set to ACTIVE.
        if cellInfo.reqNum == 3:
            for bdrSet in contUnsetBdrs:
                for bdrIdx in bdrSet:
                    Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE)
                    foundMove = True

        # If a 2-cell has continuous unset borders
        if cellInfo.reqNum == 2:
            # The board is invalid if the continuous border has a length of 3
            if len(contUnsetBdrs[0]) != 2:
                raise InvalidBoardException(f'The 2-cell {row},{col} '
                                            'must not have continous unset borders '
                                            'having length of 3 or more.')

            # If the 2-cell has continuos UNSET borders and also has at least one BLANK border,
            # then the continuous UNSET borders should be activated.
            if cellInfo.bdrBlankCount > 0:
                for bdrIdx in contUnsetBdrs[0]:
                    if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                        foundMove = True
                for bdrIdx in cellInfo.bdrIndices:
                    if bdrIdx not in contUnsetBdrs[0]:
                        if Solver.setBorder(board, bdrIdx, BorderStatus.BLANK):
                            foundMove = True
            else:
                topBdr, rightBdr, botBdr, leftBdr = cellInfo.bdrIndices

                # Smooth UL corner
                if topBdr in contUnsetBdrs[0] and leftBdr in contUnsetBdrs[0]:
                    smoothDirs = (DiagonalDirection.ULEFT, DiagonalDirection.LRIGHT)
                # Smooth UR corner
                elif topBdr in contUnsetBdrs[0] and rightBdr in contUnsetBdrs[0]:
                    smoothDirs = (DiagonalDirection.URIGHT, DiagonalDirection.LLEFT)
                # Smooth LR corner
                elif botBdr in contUnsetBdrs[0] and rightBdr in contUnsetBdrs[0]:
                    smoothDirs = (DiagonalDirection.ULEFT, DiagonalDirection.LRIGHT)
                # Smooth LL corner
                elif botBdr in contUnsetBdrs[0] and leftBdr in contUnsetBdrs[0]:
                    smoothDirs = (DiagonalDirection.URIGHT, DiagonalDirection.LLEFT)

                for smoothDir in smoothDirs:
                    foundMove = foundMove | self.handleSmoothCorner(board, cellInfo, smoothDir)

        return foundMove

    def processBorder(self, board: Board, borderIdx: int) -> bool:
        """
        Check a border for clues. Returns true if a move was found.
        Returns false otherwise.
        """
        foundMove = False
        if board.borders[borderIdx] == BorderStatus.UNSET:

            connBdrList = BoardTools.getConnectedBordersList(borderIdx)
            for connBdrIdx in connBdrList:
                if self.tools.isContinuous(board, borderIdx, connBdrIdx):
                    if board.borders[connBdrIdx] == BorderStatus.ACTIVE:
                        if Solver.setBorder(board, borderIdx, BorderStatus.ACTIVE):
                            return True

            connBdrTuple = BoardTools.getConnectedBorders(borderIdx)

            _, countActive1, countBlank1 = self.tools.getStatusCount(board, connBdrTuple[0])
            _, countActive2, countBlank2 = self.tools.getStatusCount(board, connBdrTuple[1])

            if countActive1 > 1 or countActive2 > 1:
                if Solver.setBorder(board, borderIdx, BorderStatus.BLANK):
                    return True

            if countBlank1 == len(connBdrTuple[0]) or countBlank2 == len(connBdrTuple[1]):
                if Solver.setBorder(board, borderIdx, BorderStatus.BLANK):
                    return True

        return foundMove

    def initiatePoke(self, board: Board, origRow: int, origCol: int, dxn: DiagonalDirection) -> bool:
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
        if not board.isClone:
            self.cornerEntry[origRow][origCol][dxn] = CornerEntry.POKE

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
            return self.handleCellPoke(board, targetRow, targetCol, dxn.opposite())
        else:
            arms = BoardTools.getArms(origRow, origCol, dxn)
            assert len(arms) < 2, f'Did not expect outer cell to have more than 1 arm. ' \
                f'Cell ({origRow}, {origCol}) has {len(arms)} arms at the {dxn} corner.'
            for bdrIdx in arms:
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    return True
        return False

    def handleCellPoke(self, board: Board, row: int, col: int, dxn: DiagonalDirection) -> bool:
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

        if not board.isClone:
            self.cornerEntry[row][col][dxn] = CornerEntry.POKE
            if reqNum == 2:
                self.cornerEntry[row][col][dxn] = CornerEntry.POKE

        # If a cell is being poked at a particular corner and a border on that corner
        # is already active, remove the other border on that corner.
        bdrIdx1, bdrIdx2 = BoardTools.getCornerBorderIndices(row, col, dxn)
        bdrStat1 = board.borders[bdrIdx1]
        bdrStat2 = board.borders[bdrIdx2]
        if bdrStat1 == BorderStatus.ACTIVE:
            if Solver.setBorder(board, bdrIdx2, BorderStatus.BLANK):
                foundMove = True
        elif bdrStat2 == BorderStatus.ACTIVE:
            if Solver.setBorder(board, bdrIdx1, BorderStatus.BLANK):
                foundMove = True

        if foundMove:
            return True

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
            foundMove = foundMove | self.initiatePoke(board, row, col, dxn.opposite())

        # If a 3-cell is poked, the borders opposite the poked corner should be activated.
        elif reqNum == 3:
            borders = BoardTools.getCornerBorderIndices(row, col, dxn.opposite())
            for bdrIdx in borders:
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    foundMove = True
            # Check if there is an active arm from the poke direction.
            # If there is, remove the other arms from that corner.
            arms = BoardTools.getArms(row, col, dxn)
            countUnset, countActive, _ = self.tools.getStatusCount(board, arms)

            # The board is invalid if the number of active arms is more than 1
            if countActive > 1:
                raise InvalidBoardException(f'A poked 3-cell cannot have more than two active arms: {row},{col}')

            if countActive == 1 and countUnset > 0:
                for bdrIdx in arms:
                    if board.borders[bdrIdx] == BorderStatus.UNSET:
                        if Solver.setBorder(board, bdrIdx, BorderStatus.BLANK):
                            foundMove = True

        if not foundMove:
            # As a general case, check if the poke should activate a lone border.
            bdrIdx1, bdrIdx2 = BoardTools.getCornerBorderIndices(row, col, dxn)
            if board.borders[bdrIdx1] == BorderStatus.BLANK:
                if Solver.setBorder(board, bdrIdx2, BorderStatus.ACTIVE):
                    foundMove = True
            elif board.borders[bdrIdx2] == BorderStatus.BLANK:
                if Solver.setBorder(board, bdrIdx1, BorderStatus.ACTIVE):
                    foundMove = True

        if not foundMove:
            # Get all arms of the cell except for the direction that was poked.
            otherArms: list[int] = []
            for otherDxn in DiagonalDirection:
                if otherDxn == dxn:
                    continue
                otherArms.extend(BoardTools.getArms(row, col, otherDxn))

            # Count the UNSET and ACTIVE arms from all those other arms.
            countUnset, countActive, _ = self.tools.getStatusCount(board, otherArms)

            # If there is only one remaining UNSET arm, set it accordingly.
            if countUnset == 1:
                isActiveBordersEven = countActive % 2 == 0
                newStatus = BorderStatus.ACTIVE if isActiveBordersEven else BorderStatus.BLANK
                for bdrIdx in otherArms:
                    if board.borders[bdrIdx] == BorderStatus.UNSET:
                        if Solver.setBorder(board, bdrIdx, newStatus):
                            foundMove = True

        return foundMove

    def handleSmoothCorner(self, board: Board, cellInfo: CellInfo, dxn: DiagonalDirection) -> bool:
        """
        Handle the situation when a cell's corner is known to be smooth.

        A smooth corner is a corner where a poke will never occur.
        This means that this corner either has two `ACTIVE` borders or two `BLANK` borders.

        Arguments:
            board: The board.
            cellInfo: The cell information.
            dxn: The direction of the corner.

        Returns:
            True if a move was found. False otherwise.
        """
        foundMove = False
        row = cellInfo.row
        col = cellInfo.col

        if not board.isClone:
            self.cornerEntry[row][col][dxn] = CornerEntry.SMOOTH
            if cellInfo.reqNum == 2:
                self.cornerEntry[row][col][dxn.opposite()] = CornerEntry.SMOOTH

        cornerIdx1, cornerIdx2 = cellInfo.cornerBdrs[dxn]
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
        if cellInfo.reqNum == 1:
            for bdrIdx in (cornerIdx1, cornerIdx2):
                if Solver.setBorder(board, bdrIdx, BorderStatus.BLANK):
                    foundMove = True

        # A smooth corner on a 3-cell always means that both borders are ACTIVE.
        elif cellInfo.reqNum == 3:
            for bdrIdx in (cornerIdx1, cornerIdx2):
                if Solver.setBorder(board, bdrIdx, BorderStatus.ACTIVE):
                    foundMove = True

        elif cellInfo.reqNum == 2:
            # Initiate pokes on the directions where its corners isn't smooth.
            if dxn == DiagonalDirection.ULEFT or dxn == DiagonalDirection.LRIGHT:
                foundMove = foundMove | self.initiatePoke(board, row, col, DiagonalDirection.URIGHT)
                foundMove = foundMove | self.initiatePoke(board, row, col, DiagonalDirection.LLEFT)
            elif dxn == DiagonalDirection.URIGHT or dxn == DiagonalDirection.LLEFT:
                foundMove = foundMove | self.initiatePoke(board, row, col, DiagonalDirection.ULEFT)
                foundMove = foundMove | self.initiatePoke(board, row, col, DiagonalDirection.LRIGHT)
            else:
                raise ValueError(f'Invalid DiagonalDirection: {dxn}')

            # Propagate the smoothing because if a 2-cell's corner is smooth, the opposite corner is also smooth.
            targetCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn.opposite())
            if targetCellIdx is not None:
                targetRow, targetCol = targetCellIdx
                targetCellInfo = CellInfo.init(board, targetRow, targetCol)
                foundMove = foundMove | self.handleSmoothCorner(board, targetCellInfo, dxn)
            else:
                # If there is no diagonally adjacent cell, then this is an outer edge cell,
                # so we just directly remove the one arm at that direction.
                for armIdx in BoardTools.getArms(row, col, dxn.opposite()):
                    if Solver.setBorder(board, armIdx, BorderStatus.BLANK):
                        return True

        return foundMove

    def handle2CellDiagonallyOppositeActiveArms(self, board: Board, row: int, col: int) -> bool:
        """
        Handle the case when a 2-cell has active arms in opposite corners.

        Arguments:
            board: The board.
            row: The row index of the cell.
            col: The column index of the cell.

        Returns:
            True if a move was found. False otherwise.
        """
        if board.cells[row][col] != 2:
            return False

        foundMove = False
        armsUL, armsUR, armsLR, armsLL = BoardTools.getArmsOfCell(row, col)

        # INVALID: If one corner has 2 active arms and the opposite corner has at least 1 active arm.

        _, activeCount1, _ = self.tools.getStatusCount(board, armsUL)
        _, activeCount2, _ = self.tools.getStatusCount(board, armsLR)
        if activeCount1 == 1 and activeCount2 == 1:
            for bdrIdx in armsUL + armsLR:
                if board.borders[bdrIdx] == BorderStatus.UNSET:
                    Solver.setBorder(board, bdrIdx, BorderStatus.BLANK)
                    foundMove = True

        _, activeCount1, _ = self.tools.getStatusCount(board, armsUR)
        _, activeCount2, _ = self.tools.getStatusCount(board, armsLL)
        if activeCount1 == 1 and activeCount2 == 1:
            for bdrIdx in armsUR + armsLL:
                if board.borders[bdrIdx] == BorderStatus.UNSET:
                    Solver.setBorder(board, bdrIdx, BorderStatus.BLANK)
                    foundMove = True

        return foundMove

    def updateCornerEntries(self) -> None:
        """
        Update the CornerEntry types of each corner of each cell.
        """
        updateFlag = True

        def setCornerEntry(cellIdx: Optional[tuple[int, int]], dxn: DiagonalDirection,
                           newVal: CornerEntry) -> bool:
            if cellIdx is None:
                return False
            row, col = cellIdx
            if self.cornerEntry[row][col][dxn] == CornerEntry.UNKNOWN:
                self.cornerEntry[row][col][dxn] = newVal
                return True
            elif self.cornerEntry[row][col][dxn] != newVal:
                raise InvalidBoardException(f'The corner entry of cell {row},{col} '
                                            f'at direction {dxn} cannot be set to {newVal}.')
            return False

        while updateFlag:
            updateFlag = False
            for row in range(self.rows):
                for col in range(self.cols):
                    unknownDxn = None
                    countPoke = 0
                    countSmooth = 0
                    countUnknown = 0
                    for dxn in DiagonalDirection:
                        arms = BoardTools.getArms(row, col, dxn)
                        countUnset, countActive, _ = self.tools.getStatusCount(self.board, arms)

                        if countUnset == 0:
                            targetCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
                            newVal = CornerEntry.SMOOTH if countActive % 2 == 0 else CornerEntry.POKE
                            updateFlag = updateFlag | setCornerEntry((row, col), dxn, newVal)
                            updateFlag = updateFlag | setCornerEntry(targetCellIdx, dxn.opposite(), newVal)

                        if self.cornerEntry[row][col][dxn] == CornerEntry.POKE:
                            countPoke += 1
                        elif self.cornerEntry[row][col][dxn] == CornerEntry.SMOOTH:
                            countSmooth += 1
                        elif self.cornerEntry[row][col][dxn] == CornerEntry.UNKNOWN:
                            countUnknown += 1
                            unknownDxn = dxn

                        if self.cornerEntry[row][col][dxn] != CornerEntry.UNKNOWN:
                            newVal = self.cornerEntry[row][col][dxn]
                            oppCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
                            updateFlag = updateFlag | setCornerEntry(oppCellIdx, dxn.opposite(), newVal)

                    if countUnknown == 1:
                        newCornerEntry = CornerEntry.SMOOTH if countPoke % 2 == 0 else CornerEntry.POKE
                        updateFlag = updateFlag | setCornerEntry((row, col), unknownDxn, newCornerEntry)

    def solveUsingCornerEntryInfo(self) -> bool:
        """
        Update the CornerEntry types of each corner of each cell,
        then use that information to try to solve for their borders.

        This can only be performed on the main board, not on a clone.

        Returns:
            True if a move was found. False otherwise.
        """
        foundMove = False
        self.updateCornerEntries()
        for row in range(self.rows):
            for col in range(self.cols):
                cellInfo = CellInfo.init(self.board, row, col)
                if cellInfo.bdrUnsetCount > 0:
                    for dxn in DiagonalDirection:
                        if self.cornerEntry[row][col][dxn] == CornerEntry.POKE:
                            if self.initiatePoke(self.board, row, col, dxn):
                                foundMove = True
                        elif self.cornerEntry[row][col][dxn] == CornerEntry.SMOOTH:
                            if self.handleSmoothCorner(self.board, cellInfo, dxn):
                                foundMove = True
        return foundMove

    @ cache
    def getDiagAdj2Cells(self, row: int, col: int) \
            -> dict[DiagonalDirection, Optional[tuple[int, int]]]:
        """
        Get the target cell's diagonally adjacent 2-cells.

        Arguments:
            row: The row index of the cell.
            col: The column index of the cell.

        Returns:
            A dictionary with DiagonalDirections as keys.
            The values will be a list of the adjacent 2-cell's cell index.
        """
        adj2Cells: dict[DiagonalDirection, Optional[tuple[int, int]]] = {}
        for dxn in DiagonalDirection:
            cellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
            if cellIdx is not None and self.board.cells[cellIdx[0]][cellIdx[1]] == 2:
                adj2Cells[dxn] = (cellIdx[0], cellIdx[1])
            else:
                adj2Cells[dxn] = None
        return adj2Cells
