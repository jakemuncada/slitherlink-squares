"""Main file."""

import re
from typing import Optional

from .control import Control
from .puzzle.board import Board
from .puzzle.puzzles import puzzles
from .puzzle.board_tools import BoardTools
from src.puzzle.solver.solver import Solver

BOARD_IDX = 5

TEST_LOOPS = 50

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

    _totalSolve = 0.0
    _initialSolve = 0.0
    _totalGuesses = 0
    _correctGuesses = 0

    for i in range(loops):
        board, answer = createBoard(idx)
        solver = Solver(board)
        solver.isVerbose = False
        stats = solver.solveBoardFromScratch()
        print(f'#{i + 1}:', stats)

        if board.getBordersString() != answer:
            raise ValueError('Board result is not equal to answer.')

        _totalSolve += stats.totalSolveTime
        _initialSolve += stats.initialSolveTime
        _correctGuesses += stats.correctGuessCount
        _totalGuesses += stats.totalGuessCount

    print('############################')
    print('Average initial solve time: {:.3f} seconds'.format(_initialSolve / float(loops)))
    print('Average solve time: {:.3f} seconds'.format(_totalSolve / float(loops)))
    print('Average guess count: {:.3f} guesses'.format(float(_totalGuesses) / float(loops)))
    print('Average correct guess count: {:.3f} guesses'.format(float(_correctGuesses) / float(loops)))
    print('############################')

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
