"""
This submodule contains the tools to solve the board
by guessing.
"""

import time
import random
from typing import Callable, Optional, Union

from src.puzzle.board import Board
from src.puzzle.board_tools import BoardTools
from src.puzzle.solver.solve_stats import SolveStats
from src.puzzle.enums import BorderStatus, CardinalDirection, InvalidBoardException, OptInt


# A Move consists of a border index and its BorderStatus.
Move = tuple[int, BorderStatus]

# A CellGroupGuess consists of the the cell's row, the cell's column, and its cell group.
CellGroupGuess = tuple[int, int, int]

# A generic guess can be guessing the a border's status or guessing a cell's group.
Guess = Union[Move, CellGroupGuess]


class Guesser:
    """
    The class responsible for guessing correct moves.
    """

    def __init__(self, board: Board, solve: Callable, updateUI: Callable,
                 isVerbose: bool) -> None:
        self.board = board
        self.currCellGroupGuessIdx = 0
        self.currBorderGuessIdx = 0
        self.solve = solve
        self.updateUI = updateUI
        self.isVerbose = isVerbose
        self.cellGroupGuesses: list[CellGroupGuess] = []
        self.borderGuesses: list[Move] = []
        self.guessMode = 0

    def guess(self, solveStats: SolveStats) -> bool:
        """
        Tries to find a correct configuration of the board by guessing.
        The guess may be changing an `UNSET` border to `BLANK` or `ACTIVE`,
        or it may be changing a cell's cell group.

        If such a configuration was found, the board is set to that configuration.

        Arguments:
            solveStats: The solve statistics object.

        Returns:
            True if a correct configuration was found. False otherwise.
        """

        if self.currBorderGuessIdx >= len(self.borderGuesses):
            self.borderGuesses = self.getBorderGuesses(self.board)
        if self.guessBorders(solveStats):
            return True
        return False

        ##################################################################
        # NOTE: The cell group guessing implementation (below) is slower.
        ##################################################################
        # if self.guessMode == 0:
        #     self.guessMode = 1
        #     if len(self.cellGroupGuesses) == 0:
        #         self.cellGroupGuesses = self.getCellGroupGuesses(self.board)
        #     if self.guessCellGroup(solveStats):
        #         return True

        # if self.guessMode == 1:
        #     self.guessMode = 0
        #     if len(self.borderGuesses) == 0:
        #         self.borderGuesses = self.getBorderGuesses(self.board)
        #     if self.guessBorders(solveStats):
        #         return True

        # return False

    def guessCellGroup(self, solveStats: SolveStats) -> bool:
        """
        Guess a cell's cell group and determine if this is valid or invalid.
        If the guessed cell group results in an invalid board, the opposite cell group
        must be the correct one. 

        If a correct cell group was found, the board is updated.

        Arguments:
            solveStats: The solve statistics object.

        Returns:
            True if such a cell group was found. False otherwise.
        """
        t0 = time.time()

        correctCellGroupGuess, guessCount = self.getCorrectCellGroupByGuessing()
        solveStats.totalGuessCount += guessCount

        if correctCellGroupGuess is not None:
            row, col, cellGroup = correctCellGroupGuess
            if self.board.cellGroups[row][col] is not None:
                raise AssertionError(f'Tried to set the cell group of {row},{col} '
                                     f'to {cellGroup} but it was not None.')

            # print(f'Setting {row},{col} to {cellGroup}')
            self.board.cellGroups[row][col] = cellGroup
            timeToFindMove = time.time() - t0
            solveStats.guessTimes.append(timeToFindMove)
            return True

        return False

    def guessBorders(self, solveStats: SolveStats) -> bool:
        """
        Guess the next correct move by trying to change `UNSET` borders to `BLANK` or `ACTIVE`.
        If the guessed move results in an invalid board, the opposite move must be the correct one.
        If a correct move was found, the board is updated.

        Arguments:
            solveStats: The solve statistics object.

        Returns:
            True if a move was found. False otherwise.
        """
        t0 = time.time()

        correctMove, guessCount = self.getCorrectMoveByGuessing()
        solveStats.totalGuessCount += guessCount

        if correctMove is not None:
            bdrIdx, newStatus = correctMove
            if self.board.borders[bdrIdx] != BorderStatus.UNSET:
                raise AssertionError(f'Tried to set border {bdrIdx} to {newStatus} '
                                     'but it was not UNSET.')

            self.board.borders[bdrIdx] = newStatus
            timeToFindMove = time.time() - t0
            solveStats.guessTimes.append(timeToFindMove)
            return True

        return False

    def getCorrectCellGroupByGuessing(self) -> tuple[Optional[tuple[int, int, int]], int]:
        """
        Get a correct move by guessing.

        Returns:
            The correct cell group guess and the number of guesses it made.
        """
        guessCount = 0
        while self.currCellGroupGuessIdx < len(self.cellGroupGuesses):
            # Get a guess from the list.
            row, col, newCellGroup = self.cellGroupGuesses[self.currCellGroupGuessIdx]

            if self.board.cellGroups[row][col] is None:

                # Once a guess is decided, clone the board so that the original board
                # isn't affected by the guess.
                cloneBoard = self.board.clone()

                # Then, reflect the guess on the cloned board.
                cloneBoard.cellGroups[row][col] = newCellGroup
                guessCount += 1

                # After that, we try to solve the board according to the guess.
                isValid, _ = self.solve(cloneBoard, self.updateUI)

                # If the guess resulted in an invalid board,
                # then the opposite cell group should be the correct one.
                if not isValid:
                    correctGuess = (row, col, 1 if newCellGroup == 0 else 0)
                    return correctGuess, guessCount

            # If the guess resulted to a valid board, we cannot conclude anything,
            # so we just continue to the next guess.
            self.currCellGroupGuessIdx += 1

        return None, guessCount

    def getCorrectMoveByGuessing(self) -> tuple[Optional[Move], int]:
        """
        Get a correct move by guessing.

        Returns:
            The correct move and the number of guesses it made.
        """
        guessCount = 0
        while self.currBorderGuessIdx < len(self.borderGuesses):
            # Get a guess from the list.
            guessBdrIdx, guessStatus = self.borderGuesses[self.currBorderGuessIdx]

            if self.board.borders[guessBdrIdx] == BorderStatus.UNSET:

                # Once a guess is decided, clone the board so that the original board
                # isn't affected by the guess.
                cloneBoard = self.board.clone()

                # Then, reflect the guess on the cloned board.
                cloneBoard.borders[guessBdrIdx] = guessStatus
                guessCount += 1

                # After that, we try to solve the board according to the guess.
                isValid, _ = self.solve(cloneBoard, self.updateUI)

                # If the guess resulted in an invalid board,
                # then the opposite move should be the correct one.
                if not isValid:
                    correctGuess = (guessBdrIdx, guessStatus.opposite())
                    return correctGuess, guessCount

            # If the guess resulted to a valid board, we cannot conclude anything,
            # so we just continue to the next guess.
            self.currBorderGuessIdx += 1

        return None, guessCount

    def getCellGroupGuesses(self, board: Board) -> list[tuple[int, int, int]]:
        """
        Get a list of cell groups to guess.
        """
        t0 = time.time()
        doneCells: set[tuple[int, int]] = set()
        guesses: list[tuple[int, tuple[int, int, int]]] = []
        for row in range(board.rows):
            for col in range(board.cols):

                if (row, col) in doneCells:
                    continue

                if board.cellGroups[row][col] is None:
                    connCells = self._getConnectedCells(board, row, col, set())
                    doneCells = doneCells.union(connCells)
                    size = len(connCells)
                    if size > 3:
                        guesses.append((size, (row, col, 1)))
                        guesses.append((size, (row, col, 0)))

        guesses.sort(key=lambda g: -g[0])
        result = list(map(lambda g: g[1], guesses))
        print('getCellGroupGuesses: {} [{:.3f} seconds]'.format(len(result), time.time() - t0))
        return result

    def _getConnectedCells(self, board: Board, row: int, col: int,
                           connCells: set[tuple[int, int]]) -> set[tuple[int, int]]:
        """
        Get all the cells of the same cell group adjacent to each other.

        Arguments:
            board: The board.
            row: The row index of the target cell.
            col: The column index of the target cell.
            connCells: The set of connected cells.

        Returns:
            The set of cell indices of all cells connected to the target cell.
        """
        if (row, col) in connCells:
            return connCells
        connCells.add((row, col))
        for dxn in CardinalDirection:
            if board.getBorderStatus(row, col, dxn) == BorderStatus.BLANK:
                adjRow, adjCol = BoardTools.getCellIdxOfAdjCell(row, col, dxn)
                if adjRow is not None and adjCol is not None:
                    self._getConnectedCells(board, adjRow, adjCol, connCells)
        return connCells

    def getBorderGuesses(self, board: Board) -> list[tuple[int, BorderStatus]]:
        """
        Get a list of borders to guess.
        """
        doneBorders: set[int] = set()
        highPrio: list[tuple[int, BorderStatus]] = []
        lowPrio: list[tuple[int, BorderStatus]] = []

        for row in range(board.rows):
            for col in range(board.cols):
                for dxn in CardinalDirection:
                    bdrIdx = BoardTools.getBorderIdx(row, col, dxn)
                    if board.borders[bdrIdx] == BorderStatus.UNSET:
                        doneBorders.add(bdrIdx)
                        if board.cells[row][col] == 1:
                            highPrio.append((bdrIdx, BorderStatus.ACTIVE))
                        elif board.cells[row][col] == 3:
                            highPrio.append((bdrIdx, BorderStatus.BLANK))

        for bdrIdx in range(len(board.borders)):
            if bdrIdx not in doneBorders:
                if board.borders[bdrIdx] == BorderStatus.UNSET:
                    lowPrio.append((bdrIdx, BorderStatus.ACTIVE))

        random.shuffle(highPrio)
        random.shuffle(lowPrio)

        return highPrio + lowPrio
