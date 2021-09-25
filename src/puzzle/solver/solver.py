"""
Solver for Slitherlink-Squares.
"""

import time
import cProfile as profile
from typing import Callable, Optional

from src.puzzle.board import Board
from src.puzzle.cell_info import CellInfo
from src.puzzle.board_tools import BoardTools
from src.puzzle.solver.tools import SolverTools
from src.puzzle.solver.initial import solveInit
from src.puzzle.solver.sub.guess import Guesser
from src.puzzle.solver.solve_stats import SolveStats
from src.puzzle.enums import BorderStatus, CardinalDirection, \
    DiagonalDirection, InvalidBoardException


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
        from src.puzzle.solver.sub.poke import checkOuterCellPoking
        from src.puzzle.solver.sub.loop import removeLoopMakingMove
        from src.puzzle.solver.sub.cell_group import checkCellGroupClues
        from src.puzzle.solver.sub.poke import solveUsingCornerEntryInfo
        from src.puzzle.solver.sub.cont_unset import checkCellForContinuousUnsetBorders

        self.initiatePoke = initiatePoke
        self.handleCellPoke = handleCellPoke
        self.isCellPokingAtDir = isCellPokingAtDir
        self.handleSmoothCorner = handleSmoothCorner
        self.checkCellGroupClues = checkCellGroupClues
        self.checkOuterCellPoking = checkOuterCellPoking
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

    ###########################################################################
    # SET BORDER
    ###########################################################################

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

    ###########################################################################
    # SOLVE INITIAL BOARD
    ###########################################################################

    def solveInitial(self) -> None:
        """
        Solve the initial clues.
        """
        self.board.reset()
        solveInit(self.board)
        self.initialized = True

    ###########################################################################
    # PROFILING
    ###########################################################################

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

    ###########################################################################
    # SOLVE CURRENT BOARD
    ###########################################################################

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
            # print('Still has {} guesses afterwards.'.format(len(self.getGuesses())))
            print('##################################################')

    ###########################################################################
    # SOLVE BOARD FROM SCRATCH
    ###########################################################################

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

    ###########################################################################
    # MAIN SOLVE LOOP
    ###########################################################################

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

                if self.solveClues(board):
                    moveFound = True

                if self.checkCellGroupClues(board, self.prioCells):
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

    ###########################################################################
    # SOLVE CLUES (CELLS & BORDERS)
    ###########################################################################

    def solveClues(self, board: Board) -> bool:
        """
        Solve the obvious borders. Returns true if a move was found. Returns false otherwise.
        """
        foundMove = False
        processedBorders: set[int] = set()

        for cellIdx in self.prioCells:
            row, col = cellIdx
            cellInfo = CellInfo.init(board, row, col)
            if self.processCell(board, cellInfo):
                foundMove = True

            if cellInfo.bdrUnsetCount > 1:
                for dxn in CardinalDirection:
                    borderIdx = cellInfo.bdrIndices[dxn]
                    if not borderIdx in processedBorders:
                        processedBorders.add(borderIdx)
                        if self.processBorder(board, borderIdx):
                            foundMove = True

        return foundMove

    ###########################################################################
    # PROCESS CELL
    ###########################################################################

    def processCell(self, board: Board, cellInfo: CellInfo) -> bool:
        """
        Checks a cell for clues.

        Arguments:
            board: The board.
            cellInfo: The cell information.

        Returns:
            True if a move was found. False otherwise.
        """
        foundMove = False
        row = cellInfo.row
        col = cellInfo.col

        if cellInfo.bdrActiveCount == 4:
            raise InvalidBoardException(f'Cell {row},{col} has 4 active borders.')

        if not board.isClone and cellInfo.bdrActiveCount == 3 and cellInfo.bdrUnsetCount == 1:
            for bdrIdx in cellInfo.unsetBorders:
                Solver.setBorder(board, bdrIdx, BorderStatus.BLANK)
                return True

        if cellInfo.reqNum is not None:

            if cellInfo.bdrActiveCount > cellInfo.reqNum:
                raise InvalidBoardException(f'Cell {row},{col} has {cellInfo.bdrActiveCount} '
                                            f'active borders but requires only {cellInfo.reqNum}.')

            if cellInfo.bdrUnsetCount + cellInfo.bdrActiveCount < cellInfo.reqNum:
                raise InvalidBoardException(f'Cell {row},{col} only has {cellInfo.bdrUnsetCount} '
                                            'unset borders which is not enough to get to '
                                            f'the {cellInfo.reqNum} requirement.')

            if self.fillOrRemoveRemainingUnsetBorders(board, cellInfo):
                foundMove = True

            if cellInfo.reqNum == 3:
                # If the 3-cell has an active arm, poke it.
                for dxn in DiagonalDirection:
                    armsStatus = board.getArmsStatus(row, col, dxn)
                    if any(status == BorderStatus.ACTIVE for status in armsStatus):
                        if self.handleCellPoke(board, row, col, dxn):
                            foundMove = True

        if row == 0 or row == board.rows - 1 or col == 0 or col == board.cols - 1:
            if self.checkOuterCellPoking(board, cellInfo):
                foundMove = True

        if cellInfo.reqNum == 3 and cellInfo.bdrUnsetCount > 0:
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

        if cellInfo.reqNum == 2 and cellInfo.bdrBlankCount == 1 and cellInfo.bdrUnsetCount > 0:
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

        for dxn in DiagonalDirection:
            if (row, col, dxn) not in board.pokes:
                if self.isCellPokingAtDir(board, cellInfo, dxn):
                    if self.initiatePoke(board, row, col, dxn):
                        foundMove = True

        if self.checkCellForContinuousUnsetBorders(board, cellInfo):
            foundMove = True

        return foundMove

    ###########################################################################
    # PROCESS BORDER
    ###########################################################################

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

    ###########################################################################
    # SOLVE BY GUESSING
    ###########################################################################

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

        guesser = Guesser(self.board, self._solve, updateUI, self.isVerbose)

        # Continue guessing until the board is completed.
        while True:
            if updateUI:
                updateUI()

            foundMove = guesser.guess(solveStats)

            # If at this point, a correct guess was not found, the solving has failed.
            # This is considered an error because we assume that all possible moves
            # have been tried and so we expect that there will always be a correct guess.
            if not foundMove:
                if self.isVerbose:
                    print('##################################################')
                    print('ERROR: Could not find a correct guess.')
                    print('##################################################')
                solveStats.err = 'Could not find a correct guess.'
                solveStats.endTime = time.time()
                return solveStats

            # We try to solve the rest of the clues now that a viable move was found.
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

    ###########################################################################
    # VALIDATION
    ###########################################################################

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

    ###########################################################################
    # MISCELLANEOUS
    ###########################################################################

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
