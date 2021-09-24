"""
Solver for Slitherlink-Squares.
"""

import time
import random
import cProfile as profile
from typing import Callable, Optional

from src.puzzle.board import Board
from src.puzzle.cell_info import CellInfo
from src.puzzle.board_tools import BoardTools
from src.puzzle.solver.tools import SolverTools
from src.puzzle.solver.initial import solveInit
from src.puzzle.solver.solve_stats import SolveStats
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
        self.initialized = False
        self.isVerbose = True
        self.prioCells: list[tuple[int, int]] = []
        self.threeCells: set[int] = set()
        self.initializePrioritizedCellList()
        self.initializeSubmoduleMethods()

    def initializeSubmoduleMethods(self) -> None:
        from src.puzzle.solver.sub.poke import initiatePoke
        from src.puzzle.solver.sub.poke import handleCellPoke
        from src.puzzle.solver.sub.poke import isCellPokingAtDir
        from src.puzzle.solver.sub.poke import handleSmoothCorner
        from src.puzzle.solver.sub.loop import removeLoopMakingMove
        from src.puzzle.solver.sub.poke import solveUsingCornerEntryInfo
        from src.puzzle.solver.sub.cont_unset import checkCellForContinuousUnsetBorders

        self.initiatePoke = initiatePoke
        self.handleCellPoke = handleCellPoke
        self.isCellPokingAtDir = isCellPokingAtDir
        self.handleSmoothCorner = handleSmoothCorner
        self.removeLoopMakingMove = removeLoopMakingMove
        self.solveUsingCornerEntryInfo = solveUsingCornerEntryInfo
        self.checkCellForContinuousUnsetBorders = checkCellForContinuousUnsetBorders

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
                if reqNum == 1:
                    highPrio.append((row, col))
                elif reqNum == 2:
                    medPrio.append((row, col))
                elif reqNum == 3:
                    highPrio.append((row, col))
                    self.threeCells.add((row, col))
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

    def solveInitial(self) -> None:
        """
        Solve the initial clues.
        """
        self.board.reset()
        solveInit(self.board)
        self.initialized = True

    def profileFromScratch(self) -> None:
        """
        Use cProfile to benchmark/profile solveBoardFromScratch.
        """
        profile.runctx('self.solveBoardFromScratch()', globals(), locals())

    def profileCurrentBoard(self) -> None:
        """
        Use cProfile to benchmark/profile solveCurrentBoard.
        """
        profile.runctx('self.solveCurrentBoard()', globals(), locals())

    def invalidInitialSolve(self, isComplete: bool, solveStats: SolveStats) -> SolveStats:
        """
        Print the error message and return the SolveStats.

        Arguments:
            isComplete: Whether the board was completed or not.
            solveStats: The statistics of the solve.
        """
        solveStats.solved = False
        solveStats.endTime = time.time()

        if not isComplete:
            if self.isVerbose:
                print('##################################################')
                print('ERROR: The initial solve [{:.3f} seconds] unexpectedly resulted '
                      'in an invalid board.'.format(solveStats.initialSolveTime))
                print('##################################################')
            solveStats.err = 'The initial solve unexpectedly resulted in an invalid board.'
        else:
            if self.isVerbose:
                print('##################################################')
                print('ERROR: The initial solve [{:.3f} seconds] completed the board '
                      'but was invalid.'.format(solveStats.initialSolveTime))
                print('##################################################')
            solveStats.err = 'The initial solve completed the board but was invalid.'

        return solveStats

    def solveBoardFromScratch(self, updateUI: Callable = None) -> SolveStats:
        """
        Solve board from scratch.
        Returns the statistics of the solve.
        """
        self.board.reset()

        solveStats = SolveStats()

        solveInit(self.board)
        self.initialized = True

        if updateUI:
            updateUI()

        # Try to solve the board. This is the initial solve.
        isValid, initialSolveTime = self._solve(self.board, updateUI)
        if self.isVerbose:
            print('Initial solve: {:.3f} seconds'.format(initialSolveTime))
        solveStats.initialSolveTime = initialSolveTime

        # The initial solve must not result in an invalid board.
        if not isValid:
            return self.invalidInitialSolve(False, solveStats)

        # Get the set of remaining UNSET borders.
        unsetBorders: set[int] = set()
        for bdrIdx in range(len(self.board.borders)):
            if self.board.borders[bdrIdx] == BorderStatus.UNSET:
                unsetBorders.add(bdrIdx)
        solveStats.unsetBorderCountAfterInitialSolve = len(unsetBorders)

        # If there are no more UNSET borders, the board is complete.
        if len(unsetBorders) == 0:

            # If the board passes the validation, the board has been successfully solved.
            if self.simpleValidation(self.board):
                if self.isVerbose:
                    print('##################################################')
                    print('Solving the board from scratch took {:.3f} seconds '
                          'without needing to guess.'.format(initialSolveTime))
                    print('##################################################')

                solveStats.solved = True
                solveStats.initialSolveTime = initialSolveTime
                solveStats.endTime = time.time()
                return solveStats

            # Otherwise, if the board did NOT pass the validation,
            # there must be something wrong with the Solver.
            else:
                return self.invalidInitialSolve(True, solveStats)

        # If the board has not been solved after the initial solve, try to guess moves.
        solveStats = self.solveBoardByGuessing(unsetBorders, solveStats, updateUI)

        if solveStats.solved and self.isVerbose:
            print('##################################################')
            print('Solving the board from scratch took {:.3f} seconds '
                  'with {} guesses, {} of which were correct.'
                  .format(solveStats.totalSolveTime, solveStats.totalGuessCount,
                          solveStats.correctGuessCount))
            print('##################################################')

        return solveStats

    def solveBoardByGuessing(self, unsetBorders: Optional[set[int]],
                             solveStats: Optional[SolveStats] = None,
                             updateUI: Optional[Callable] = None) -> SolveStats:
        """
        Solve the given board by guessing moves.

        Arguments:
            unsetBorders: The set of border indices of the remaining UNSET borders. Optional.
            solveStats: The statistics of the solve. Optional.
            updateUI: The method to redraw the board onto the screen. Optional.
        """
        isStandalone = False
        if solveStats is None:
            solveStats = SolveStats()
            isStandalone = True

        if unsetBorders is None:
            unsetBorders: set[int] = set()
            for bdrIdx in range(len(self.board.borders)):
                if self.board.borders[bdrIdx] == BorderStatus.UNSET:
                    unsetBorders.add(bdrIdx)

        currGuessIdx = 0
        guessList: list[tuple[int, BorderStatus]] = []

        # Continue guessing until the board is completed.
        while True:
            t1 = time.time()

            if updateUI:
                updateUI()

            # Update the guess list
            if currGuessIdx >= len(guessList):
                currGuessIdx = 0
                guessList = self.getGuesses()
                if self.isVerbose:
                    print(f'Number of guesses found: {len(guessList)}')

            correctGuess: Optional[tuple[int, BorderStatus]] = None

            while currGuessIdx < len(guessList):
                # Get a guess move from the list and check if it is still currently UNSET.
                guessBdrIdx, guessStatus = guessList[currGuessIdx]
                if self.board.borders[guessBdrIdx] == BorderStatus.UNSET:

                    # Once a move is found, clone the board so that the original board
                    # isn't affected by the guess.
                    cloneBoard = self.board.clone()

                    # Then, reflect the guess on the cloned board.
                    Solver.setBorder(cloneBoard, guessBdrIdx, guessStatus)
                    solveStats.totalGuessCount += 1

                    # After that, we try to solve the board according to the guess.
                    isValid, timeElapsed = self._solve(cloneBoard, updateUI)

                    # If the guess resulted in an invalid board,
                    # then the opposite move should be the correct one.
                    if not isValid:
                        # We set the correct status of the border in the original board.
                        Solver.setBorder(self.board, guessBdrIdx, guessStatus.opposite())
                        # Record the guess and update the statistics.
                        correctGuess = (guessBdrIdx, guessStatus.opposite())
                        timeToFindCorrectGuess = time.time() - t1
                        solveStats.guessTimes.append(timeToFindCorrectGuess)

                        if self.isVerbose:
                            print('Guess #{}: border {} to {} [{:.3f} seconds]'.format(
                                solveStats.totalGuessCount,
                                guessBdrIdx,
                                guessStatus.opposite(),
                                timeToFindCorrectGuess))
                        break

                # If the guess resulted to a valid board, we cannot conclude anything,
                # so we just continue to the next guess.
                currGuessIdx += 1

            # If at this point, a correct guess was not found, restart the loop.
            if correctGuess is None:
                continue

            # After we have found a guess that resulted in an invalid board,
            # only that particular border was set, so from that, we try to solve
            # the rest of the borders (this time on the original board).
            isValid, timeElapsed = self._solve(self.board, updateUI)
            if self.isVerbose:
                print('Solve: {:.3f} seconds'.format(timeElapsed))

            # At this point, if the board is invalid, then something is wrong with the Solver.
            if not isValid:
                if self.isVerbose:
                    print('##################################################')
                    print('ERROR: The supposedly correct guess unexpectedly resulted in an invalid board.')
                    print('##################################################')
                solveStats.err = 'The supposedly correct guess unexpectedly resulted in an invalid board.'
                solveStats.endTime = time.time()
                return solveStats

            # Update the set of UNSET borders.
            for bdrIdx in unsetBorders.copy():
                if self.board.borders[bdrIdx] != BorderStatus.UNSET:
                    unsetBorders.remove(bdrIdx)

            # If there are still some UNSET borders, continue guessing.
            if len(unsetBorders) > 0:
                continue

            # If there are no more UNSET borders, the board is complete.
            # If the board passes the validation, the board has been successfully solved.
            if self.simpleValidation(self.board):
                solveStats.solved = True
                solveStats.endTime = time.time()

                if isStandalone and self.isVerbose:
                    print('##################################################')
                    print('Solving the board [{:.3f} seconds] took {} guesses, '
                          '{} of which were correct.'.format(solveStats.totalSolveTime,
                                                             solveStats.totalGuessCount, solveStats.correctGuessCount))
                    print('##################################################')

            # Otherwise, if the board did NOT pass the validation,
            # there must be something wrong with the Solver.
            else:
                if self.isVerbose:
                    print('##################################################')
                    print('ERROR: The supposedly correct guess '
                          'unexpectedly resulted in an invalid board.')
                    print('##################################################')
                solveStats.err = 'The supposedly correct guess ' \
                    'unexpectedly resulted in an invalid board.'
                solveStats.endTime = time.time()

            return solveStats

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

        # if len(highPrio) + len(lowPrio) == 0:
        #     if self.board.isComplete:
        #         return []
        #     raise AssertionError('The board is not yet complete, but no guesses were found.')

        return highPrio + lowPrio

    def solveCurrentBoard(self, updateUI: Callable = None) -> SolveStats:
        """
        Solve the board starting from its current state.
        """
        solveStats = SolveStats()
        if not self.initialized:
            solveInit(self.board)
            self.initialized = True
            if updateUI:
                updateUI()

        isValid, timeElapsed = self._solve(self.board, updateUI)

        solveStats.endTime = time.time()
        solveStats.initialSolveTime = timeElapsed
        solveStats.err = None if isValid else 'The resulting board is not valid.'

        if self.isVerbose:
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
                moveFound = False

                if self.solveObvious(board):
                    moveFound = True

                self.updateCellGroups(board)
                if self.checkCellGroupClues(board):
                    moveFound = True

                if self.removeLoopMakingMove(board):
                    moveFound = True

                if not board.isClone:
                    if self.solveUsingCornerEntryInfo(board):
                        moveFound = True

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

        isComplete = True
        activeBorderCount = 0
        startActiveBdrIdx = 0

        for bdrIdx in range(len(board.borders)):
            bdrStat = board.borders[bdrIdx]

            if bdrStat == BorderStatus.UNSET:
                isComplete = False

            elif bdrStat == BorderStatus.ACTIVE:
                activeBorderCount += 1
                startActiveBdrIdx = bdrIdx
                conn = BoardTools.getConnectedBorders(bdrIdx)

                _, conn0Active, conn0Blank = SolverTools.getStatusCount(board, conn[0])
                _, conn1Active, conn1Blank = SolverTools.getStatusCount(board, conn[1])

                # Active borders must not be floating,
                # i.e. unconnected to any other border.
                if conn0Blank == len(conn[0]):
                    return False
                if conn1Blank == len(conn[1]):
                    return False

                # An active border cannot form an intersection
                # with more than one other active border.
                if conn0Active > 1:
                    return False
                if conn1Active > 1:
                    return False

        # If the board is not yet complete, we won't perform the remaining check.
        if not isComplete:
            return True

        # If the board is complete, we check if all the ACTIVE borders are connected.
        connectedBorders: set[int] = set()

        def _addBorder(bdrIdx: int):
            if bdrIdx in connectedBorders:
                return
            connectedBorders.add(bdrIdx)
            for connBdrIdx in BoardTools.getConnectedBordersList(bdrIdx):
                if board.borders[connBdrIdx] == BorderStatus.ACTIVE:
                    _addBorder(connBdrIdx)

        _addBorder(startActiveBdrIdx)

        # When the board is complete, it is valid if and only if
        # the ACTIVE borders are connected to each other to form one big loop.
        return len(connectedBorders) == activeBorderCount

    def updateCellGroups(self, board: Board) -> None:
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

    def checkCellGroupClues(self, board: Board) -> bool:
        """
        If the cell group ID of two adjacent cells are not equal,
        the border between them should be set to `ACTIVE`.
        If the cell group ID's are equal, the border should be set to `BLANK`.
        """
        foundMove = False
        def fromAdj(isAdjEqual): return BorderStatus.BLANK if isAdjEqual else BorderStatus.ACTIVE

        for row, col in self.prioCells:
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
                        _found = _found | self.initiatePoke(board, row, col, dxn)

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
                            foundMove = foundMove | self.handleSmoothCorner(board, row, col, dxn)
                        else:
                            foundMove = foundMove | self.initiatePoke(board, row, col, dxn)

        return foundMove

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

        if not board.isClone and cellInfo.bdrActiveCount == 3 and cellInfo.bdrUnsetCount == 1:
            for bdrIdx in cellInfo.unsetBorders:
                Solver.setBorder(board, bdrIdx, BorderStatus.BLANK)
                return True

        if reqNum is not None:

            if cellInfo.bdrActiveCount > reqNum:
                raise InvalidBoardException(f'Cell {row},{col} has {cellInfo.bdrActiveCount} '
                                            f'active borders but requires only {reqNum}.')

            if cellInfo.bdrUnsetCount + cellInfo.bdrActiveCount < reqNum:
                raise InvalidBoardException(f'Cell {row},{col} only has {cellInfo.bdrUnsetCount} '
                                            'unset borders which is not enough to get to '
                                            f'the {reqNum} requirement.')

            if self.fillOrRemoveRemainingUnsetBorders(board, cellInfo):
                foundMove = True

            if reqNum == 3:
                # If the 3-cell has an active arm, poke it.
                for dxn in DiagonalDirection:
                    armsStatus = board.getArmsStatus(row, col, dxn)
                    if any(status == BorderStatus.ACTIVE for status in armsStatus):
                        if self.handleCellPoke(board, row, col, dxn):
                            foundMove = True

                if self.checkThreeTwoThreeTwoPattern(board, cellInfo):
                    foundMove = True

            elif reqNum == 2:
                if self.handle2CellDiagonallyOppositeActiveArms(board, row, col):
                    foundMove = True

        if cellInfo.reqNum is None and cellInfo.bdrActiveCount == 2 and cellInfo.bdrUnsetCount == 2:
            if self.check3CellRectanglePattern(board, cellInfo):
                foundMove = True

        if row == 0 or row == board.rows - 1 or col == 0 or col == board.cols - 1:
            if self.checkOuterCellPoking(board, cellInfo):
                foundMove = True

        if reqNum == 3 and cellInfo.bdrUnsetCount > 0:
            # Check if the 3-cell was indirectly poked by a 2-cell (poke by propagation).
            for dxn in DiagonalDirection:
                oppoDir = dxn.opposite()
                bdrStat1 = board.borders[cellInfo.cornerBdrs[oppoDir][0]]
                bdrStat2 = board.borders[cellInfo.cornerBdrs[oppoDir][1]]
                if bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.UNSET:
                    currCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
                    if SolverTools.isCellIndirectPokedByPropagation(board, currCellIdx, dxn):
                        bdrIdx1, bdrIdx2 = cellInfo.cornerBdrs[oppoDir]
                        Solver.setBorder(board, bdrIdx1, BorderStatus.ACTIVE)
                        Solver.setBorder(board, bdrIdx2, BorderStatus.ACTIVE)
                        foundMove = True

        if reqNum == 2 and cellInfo.bdrBlankCount == 1 and cellInfo.bdrUnsetCount > 0:
            for dxn in DiagonalDirection:
                oppoDir = dxn.opposite()
                bdrStat1 = board.borders[cellInfo.cornerBdrs[oppoDir][0]]
                bdrStat2 = board.borders[cellInfo.cornerBdrs[oppoDir][1]]
                if (bdrStat1 == BorderStatus.UNSET and bdrStat2 == BorderStatus.BLANK) or \
                        (bdrStat1 == BorderStatus.BLANK and bdrStat2 == BorderStatus.UNSET):
                    currCellIdx = BoardTools.getCellIdxAtDiagCorner(row, col, dxn)
                    if SolverTools.isCellIndirectPokedByPropagation(board, currCellIdx, dxn):
                        if self.handleCellPoke(board, row, col, dxn):
                            foundMove = True

        # Check every cell if it is poking a diagonally adjacent cell.
        for dxn in DiagonalDirection:
            if (row, col, dxn) not in board.pokes:
                if self.isCellPokingAtDir(board, cellInfo, dxn):
                    if self.initiatePoke(board, row, col, dxn):
                        foundMove = True

        # if not foundMove:
        if self.checkCellForContinuousUnsetBorders(board, cellInfo):
            foundMove = True

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
                if self.initiatePoke(board, row, col + 1, DiagonalDirection.URIGHT):
                    found = True
                if found | self.initiatePoke(board, row + 1, col, DiagonalDirection.LLEFT):
                    found = True

        elif row + 1 < rows and col - 1 >= 0 and board.cells[row + 1][col - 1] == 3:
            if board.cells[row][col - 1] == 2 and board.cells[row + 1][col] == 2:
                if found | self.initiatePoke(board, row, col - 1, DiagonalDirection.URIGHT):
                    found = True
                if found | self.initiatePoke(board, row + 1, col, DiagonalDirection.LLEFT):
                    found = True

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

        isTop3Cell = SolverTools.isAdjCellReqNumEqualTo(board, row, col, CardinalDirection.TOP, 3)
        isRight3Cell = SolverTools.isAdjCellReqNumEqualTo(board, row, col, CardinalDirection.RIGHT, 3)
        isBot3Cell = SolverTools.isAdjCellReqNumEqualTo(board, row, col, CardinalDirection.BOT, 3)
        isLeft3Cell = SolverTools.isAdjCellReqNumEqualTo(board, row, col, CardinalDirection.LEFT, 3)

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
                if self.handleCellPoke(board, row, col - 1, DiagonalDirection.URIGHT):
                    foundMove = True
            if col < self.cols - 1:
                if self.handleCellPoke(board, row, col + 1, DiagonalDirection.ULEFT):
                    foundMove = True

        # If the cell is a leftmost cell, check if its LEFT border is active.
        if col == 0 and cellInfo.leftBdr == BorderStatus.ACTIVE:
            if row > 0:
                if self.handleCellPoke(board, row - 1, col, DiagonalDirection.LLEFT):
                    foundMove = True
            if row < self.rows - 1:
                if self.handleCellPoke(board, row + 1, col, DiagonalDirection.ULEFT):
                    foundMove = True

        # If the cell is a rightmost cell, check if its RIGHT border is active.
        if col == self.cols - 1 and cellInfo.rightBdr == BorderStatus.ACTIVE:
            if row > 0:
                if self.handleCellPoke(board, row - 1, col, DiagonalDirection.LRIGHT):
                    foundMove = True
            if row < self.rows - 1:
                if self.handleCellPoke(board, row + 1, col, DiagonalDirection.URIGHT):
                    foundMove = True

        # If the cell is a bottommost cell, check if its BOT border is active.
        if row == self.rows - 1 and cellInfo.botBdr == BorderStatus.ACTIVE:
            if col > 0:
                if self.handleCellPoke(board, row, col - 1, DiagonalDirection.LRIGHT):
                    foundMove = True
            if col < self.cols - 1:
                if self.handleCellPoke(board, row, col + 1, DiagonalDirection.LLEFT):
                    foundMove = True

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
                if SolverTools.isContinuous(board, borderIdx, connBdrIdx):
                    if board.borders[connBdrIdx] == BorderStatus.ACTIVE:
                        if Solver.setBorder(board, borderIdx, BorderStatus.ACTIVE):
                            return True

            connBdrTuple = BoardTools.getConnectedBorders(borderIdx)

            _, countActive1, countBlank1 = SolverTools.getStatusCount(board, connBdrTuple[0])
            _, countActive2, countBlank2 = SolverTools.getStatusCount(board, connBdrTuple[1])

            if countActive1 > 1 or countActive2 > 1:
                if Solver.setBorder(board, borderIdx, BorderStatus.BLANK):
                    return True

            if countBlank1 == len(connBdrTuple[0]) or countBlank2 == len(connBdrTuple[1]):
                if Solver.setBorder(board, borderIdx, BorderStatus.BLANK):
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

        _, activeCount1, _ = SolverTools.getStatusCount(board, armsUL)
        _, activeCount2, _ = SolverTools.getStatusCount(board, armsLR)
        if activeCount1 == 1 and activeCount2 == 1:
            for bdrIdx in armsUL + armsLR:
                if board.borders[bdrIdx] == BorderStatus.UNSET:
                    Solver.setBorder(board, bdrIdx, BorderStatus.BLANK)
                    foundMove = True

        _, activeCount1, _ = SolverTools.getStatusCount(board, armsUR)
        _, activeCount2, _ = SolverTools.getStatusCount(board, armsLL)
        if activeCount1 == 1 and activeCount2 == 1:
            for bdrIdx in armsUR + armsLL:
                if board.borders[bdrIdx] == BorderStatus.UNSET:
                    Solver.setBorder(board, bdrIdx, BorderStatus.BLANK)
                    foundMove = True

        return foundMove
