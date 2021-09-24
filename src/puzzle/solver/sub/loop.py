"""
This submodule contains the tools to solve the clues
regarding loop making moves.
"""

from src.puzzle.board import Board
from src.puzzle.solver.solver import Solver
from src.puzzle.board_tools import BoardTools
from src.puzzle.enums import BorderStatus, DiagonalDirection, InvalidBoardException


def removeLoopMakingMove(board: Board) -> bool:
    """
    Find an `UNSET` border that, if set to `ACTIVE`, will create a loop.
    Since loops are prohibited, this border should be set to `BLANK`.

    Arguments:
        board: The board.

    Returns:
        True if such a border was removed. False otherwise.
    """
    borderGoupDict, activeBorders, unsetBorders = _getBorderGroupDict(board)

    foundMove = False
    for bdrIdx in unsetBorders:
        conn = BoardTools.getConnectedBorders(bdrIdx)
        group1 = None
        group2 = None
        for connBdr in conn[0]:
            if connBdr in activeBorders:
                group1 = borderGoupDict[connBdr]
                break
        for connBdr in conn[1]:
            if connBdr in activeBorders:
                group2 = borderGoupDict[connBdr]
                break

        if group1 is not None and group2 is not None and group1 == group2:
            if Solver.setBorder(board, bdrIdx, BorderStatus.BLANK):
                foundMove = True

    if foundMove:
        return True

    # if self._checkThreeCellLoopMakingMoves(board, borderGoupDict):
    #     foundMove = True

    return foundMove

def _checkThreeCellLoopMakingMoves(self, board: Board, borderGoupDict: dict[int, int]) -> bool:
    """
    Check 3-cells for the case when setting an arm to `ACTIVE` would create a loop.

    Arguments:
        board: The board.
        borderGroupDict: The dictionary containing the border group IDs.

    Returns:
        True if a move was found. False otherwise.
    """

    def _getOtherArms(cellArms: tuple[list[int], list[int], list[int], list[int]],
                        exceptDir: DiagonalDirection) -> list[int]:
        """
        Get a list of the indices of the arms except on the given direction.
        This list will only contain UNSET arms.
        """
        result: list[int] = []
        for dxn in DiagonalDirection:
            if dxn == exceptDir:
                continue
            for armIdx in cellArms[dxn]:
                if board.borders[armIdx] == BorderStatus.UNSET:
                    result.append(armIdx)
        return result

    foundMove = False
    for row, col in self.threeCells:
        cellBorders = set(BoardTools.getCellBorders(row, col))
        cellArms = BoardTools.getArmsOfCell(row, col)
        # Look at all the corners of the 3-cell.
        for dxn in DiagonalDirection:
            arms = cellArms[dxn]
            activeArmIdx = None

            # We only want to process the corner where an arm is ACTIVE.
            # So we look at the arms at this current direction,
            # and save the border index of the arm that is ACTIVE.
            for armIdx in arms:
                if board.borders[armIdx] != BorderStatus.ACTIVE:
                    continue
                if activeArmIdx is None:
                    activeArmIdx = armIdx
                else:
                    raise InvalidBoardException('The 3-cell must not have '
                                                'two ACTIVE arms on the same corner.')

            # If we haven't found an ACTIVE arm on this corner,
            # we aren't interested in this corner.
            if activeArmIdx is None:
                continue

            # We look at the UNSET arms except the arms on this direction.
            otherArms = _getOtherArms(cellArms, dxn)
            for targetArm in otherArms:
                # This targetArm is the arm that we want to make ACTIVE.
                # However, if we make it ACTIVE, it might make a loop.
                # So we determine whether this arm is connected to a border group
                # equal to the above ACTIVE arm's border group.
                willCreateLoop = False
                connList = BoardTools.getConnectedBordersList(targetArm)
                for connBdr in connList:
                    if connBdr in cellBorders:
                        continue
                    if board.borders[connBdr] != BorderStatus.ACTIVE:
                        continue
                    if borderGoupDict[connBdr] == borderGoupDict[activeArmIdx]:
                        willCreateLoop = True
                        break

                # If activating the target arm will create a loop,
                # this move would obviously be invalid. Therefore, we should make it BLANK.
                if willCreateLoop:
                    if Solver.setBorder(board, targetArm, BorderStatus.BLANK):
                        foundMove = True

    return foundMove

def _getBorderGroupDict(board: Board) -> tuple[dict[int, int], set[int], set[int]]:
    """
    Get the dictionary containing the border groups of all `ACTIVE` borders.

    Arguments:
        board: The board.

    Returns:
        A tuple containing the following:
            - The dictionary containing the border groups of all ACTIVE borders.
            - The set of all ACTIVE borders.
            - The set of all UNSET borders.
    """
    # Get all active and unset borders
    activeBorders: set[int] = set()
    unsetBorders: set[int] = set()
    for bdrIdx in range(len(board.borders)):
        if board.borders[bdrIdx] == BorderStatus.ACTIVE:
            activeBorders.add(bdrIdx)
        elif board.borders[bdrIdx] == BorderStatus.UNSET:
            unsetBorders.add(bdrIdx)

    processedBorders: set[BorderStatus] = set()
    borderGroupDict: dict[int, int] = {}

    # Set all connected active borders to the same group ID.
    def _process(idx: int, groupId: int) -> bool:
        if idx in processedBorders:
            return False
        isConnectedToUnset = False
        processedBorders.add(idx)
        borderGroupDict[idx] = groupId
        connList = BoardTools.getConnectedBordersList(idx)
        for connBdr in connList:
            if connBdr in activeBorders:
                if _process(connBdr, groupId):
                    isConnectedToUnset = True
            if connBdr in unsetBorders:
                isConnectedToUnset = True
        return isConnectedToUnset

    currId = 0
    for bdrIdx in activeBorders:
        if bdrIdx in processedBorders:
            continue
        hasConnectedUnsetBdr = _process(bdrIdx, currId)
        if not hasConnectedUnsetBdr and len(unsetBorders) > 0:
            raise InvalidBoardException('Loop detected.')
        currId += 1

    return borderGroupDict, activeBorders, unsetBorders