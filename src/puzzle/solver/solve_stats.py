"""
This module contains the SolveStats class,
which contains information about the solve.
"""

import time
from typing import Optional


class SolveStats:
    """
    A class containing information and statistics about the solve.

    Properties:
        startTime: The timestamp of when the solve was started.
        endTime: The timestamp of when the solve finished.
        solved: True if the board was solved successfully.
        initialSolveTime: The time it took the first/initial solve.
        unsetBorderCountAfterInitialSolve: The number of unset borders after the initial solve.
        totalSolveTime: The total solve time.
        totalGuessCount: The number of times the solve tried to guess a move.
        correctGuessCount: The number of correct guesses.
        guessTimes: The list containing the time it took to find each correct guess.
        err: The error string. Optional.
    """

    def __init__(self, startTime: Optional[float] = None) -> None:
        self.startTime = startTime if startTime is not None else time.time()
        self.endTime = startTime
        self.solved: bool = False
        self.initialSolveTime: float = 0.0
        self.unsetBorderCountAfterInitialSolve = 0
        self.totalGuessCount: int = 0
        self.guessTimes: list[float] = []
        self.err: Optional[str] = None

    @property
    def totalSolveTime(self) -> float:
        """
        The total time it took to solve the board.
        """
        return self.endTime - self.startTime

    @property
    def correctGuessCount(self) -> int:
        """
        The number of correct guesses.
        """
        return len(self.guessTimes)

    @property
    def aveGuessTime(self) -> float:
        """
        The average time to find a correct guess.
        """
        total: float = 0.0
        for guessTime in self.guessTimes:
            total += guessTime
        return total / float(self.totalGuessCount)

    def __str__(self) -> str:
        prefix = '{}: [Total: {:.3f}] [Initial: {:.3f}]'.format(
            'SOLVED' if self.solved else 'NOT SOLVED',
            self.totalSolveTime, self.initialSolveTime)

        if self.err is not None:
            return f'{prefix} ERROR: {self.err}'

        if not self.solved:
            return f'{prefix}'

        if self.totalGuessCount == 0:
            return f'{prefix} [NO GUESSING]'

        unsetBorderStr = f'[{self.unsetBorderCountAfterInitialSolve} unset borders]'
        guessCountStr = f'[{self.correctGuessCount} out of {self.totalGuessCount} guesses were correct]'
        guessTimeStr = '[Ave Guess Time: {:.3f}]'.format(self.aveGuessTime)
        return f'{prefix} {unsetBorderStr} {guessCountStr} {guessTimeStr}'
