"""Solver for Slitherlink-Squares."""


class Solver():
    """Solver for Slitherlink-Squares"""

    # The Board to be solved.
    board = None

    def init(self, board):
        """
        Initialize a Solver for a given board.
        """
        self.board = board

    def solve(self):
        """
        Solve the board. Returns the final status of the borders of the solved board.
        Returns None if the board cannot be solved in its current state.

        Important:
            Assumes that the board is valid at the point that this method is called.

        Returns:
            [[BorderStatus]]: A two-dimensional array containing the border status
                of the final solved board.
        """

        # Get all the UNSET borders
        unsetBorders = self.board.getUnsetBorders()

        # If the board is complete (no more UNSET borders), then the board has been solved.
        if len(unsetBorders) == 0:
            return self.board.borders

            