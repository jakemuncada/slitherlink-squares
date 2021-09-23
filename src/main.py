"""Main file."""

import re
from typing import Optional

from .control import Control
from .puzzle.board import Board
from .puzzle.puzzles import puzzles
from .puzzle.board_tools import BoardTools
from src.puzzle.solver.solver import Solver

BOARD_IDX = 5

TEST_LOOPS = 30


def main(idx: Optional[int] = None):
    """Main function."""
    idx = idx if idx is not None else BOARD_IDX
    board, _ = createBoard(idx)
    control = Control(board)
    control.start()


def test(idx: Optional[int] = None, loops: Optional[int] = None):
    """For testing the solver."""

    idx = idx if idx is not None else BOARD_IDX
    loops = loops if loops is not None else TEST_LOOPS

    loopCount = 0
    _unsetCount = None
    _totalSolve = 0.0
    _initialSolve = 0.0
    _totalGuesses = 0
    _correctGuesses = 0

    try:
        for i in range(loops):
            board, answer = createBoard(idx)
            solver = Solver(board)
            solver.isVerbose = False
            stats = solver.solveBoardFromScratch()
            print(f'#{i + 1}:', stats)

            if board.getBordersString() != answer:
                raise ValueError('Board result is not equal to answer.')

            if i == 0:
                _unsetCount = stats.unsetBorderCountAfterInitialSolve
            elif stats.unsetBorderCountAfterInitialSolve != _unsetCount:
                raise ValueError('The unset border count must be consistent.')

            _totalSolve += stats.totalSolveTime
            _initialSolve += stats.initialSolveTime
            _correctGuesses += stats.correctGuessCount
            _totalGuesses += stats.totalGuessCount
            loopCount += 1

    except KeyboardInterrupt:
        pass

    if loopCount > 0:
        print()
        print('#### __Puzzle {}:__'.format(idx))
        print('Average solve time: __{:.3f}__ seconds'.format(_totalSolve / float(loopCount)))
        print('Average initial solve time: __{:.3f}__ seconds'.format(_initialSolve / float(loopCount)))
        print('Number of unset borders: __{}__ borders'.format(_unsetCount))
        print('Average guess count: __{:.3f}__ guesses'.format(float(_totalGuesses) / float(loopCount)))
        print('Average correct guess count: __{:.3f}__ guesses'.format(float(_correctGuesses) / float(loopCount)))
        print()


def createBoard(idx: int) -> tuple[Board, str]:
    """
    Create the board.
    """
    pz = puzzles[idx]
    rows = pz["rows"]
    cols = pz["cols"]
    data = re.sub(r"\s+", "", pz["data"])
    answer = re.sub(r"\s+", "", pz["ans"]) if "ans" in pz else None

    BoardTools.rows = rows
    BoardTools.cols = cols

    return Board.fromString(rows, cols, data), answer
