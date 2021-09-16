"""
Solver for Slitherlink-Squares.
"""

import time

from src.puzzle.solver_init import solveInit
from src.puzzle.solver_tools import SolverTools
from src.puzzle.enums import BorderStatus, CardinalDirection, CellBdrs, DiagonalDirection
from src.puzzle.board import Board


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
            if not moveFound:
                moveFound = self.removeLoopMakingMove()
        
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

    def removeLoopMakingMove(self) -> bool:
        """
        Find an `UNSET` border that, if set to `ACTIVE`, will create a loop.
        Since loops are prohibited, this border should be set to `BLANK`.

        Returns:
            True if such a border was removed. False otherwise.
        """
        t0 = time.time()

        # Get all active and unset borders
        activeBorders: set[int] = set()
        unsetBorders: set[int] = set()
        for bdrIdx in range(len(self.board.borders)):
            if self.board.borders[bdrIdx] == BorderStatus.ACTIVE:
                activeBorders.add(bdrIdx)
            elif self.board.borders[bdrIdx] == BorderStatus.UNSET:
                unsetBorders.add(bdrIdx)

        processedBorders: set[BorderStatus] = set()
        borderGroup: dict[int, int] = {}

        # Set all connected active borders to the same group ID
        def _process(idx: int, groupId: int) -> None:
            if idx in processedBorders:
                return
            processedBorders.add(idx)
            borderGroup[idx] = groupId
            connList = self.board.tools.getConnectedBordersList(idx)
            for connBdr in connList:
                if connBdr in activeBorders:
                    _process(connBdr, groupId)

        currId = 0
        for bdrIdx in activeBorders:
            if bdrIdx in processedBorders:
                continue
            _process(bdrIdx, currId)
            currId += 1

        moveCount = 0
        moveFound = False
        for bdrIdx in unsetBorders:
            conn = self.board.tools.getConnectedBorders(bdrIdx)
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
                if self.setBorder(bdrIdx, BorderStatus.BLANK):
                    self.displayMoveDesc(f'Removing loop-making border: {bdrIdx}')
                    moveFound = True
                    moveCount += 1
                    break

        print('Loop-making borders: {} borders found [{:.3f} seconds]'.format(moveCount, time.time() - t0))

        return moveFound
            

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
                        self.displayMoveDesc(f'Filling up: Cell {cellIdx}')
                        foundMove = True

            elif self.tools.shouldRemoveRemainingUnsetBorders(self.board, row, col):
                for borderIdx in self.board.getUnsetBordersOfCell(row, col):
                    if self.setBorder(borderIdx, BorderStatus.BLANK):
                        self.displayMoveDesc(f'Removing remaining borders: Cell {cellIdx}')
                        foundMove = True

            if reqNum == 3:
                # If the 3-cell has an active arm, poke it.
                for dxn in DiagonalDirection:
                    armsStatus = self.board.getArmsStatus(row, col, dxn)
                    if any(status == BorderStatus.ACTIVE for status in armsStatus):
                        self.handleCellPoke(row, col, dxn)
                        break

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
                                self.displayMoveDesc(f'Removing continous borders of 1-cell: {cellIdx}')
                                foundMove = True
                
                # If a 3-cell has continuous unset borders, they should be set to ACTIVE.
                if reqNum == 3:
                    for bdrSet in contUnsetBdrs:
                        for bdrIdx in bdrSet:
                            if self.setBorder(bdrIdx, BorderStatus.ACTIVE):
                                self.displayMoveDesc(f'Activating continuous borders of 3-cell: {cellIdx}')
                                foundMove = True

                # If a 2-cell has continuous unset borders
                if reqNum == 2:

                    # INVALID: If the continuous border has a length of 3
                    assert len(contUnsetBdrs[0]) == 2, f'The 2-cell {row},{col} ' \
                        'must not have continous unset borders having length of 3 or more.'

                    # If the 2-cell has continuos UNSET borders and also has at least one BLANK border,
                    # then the continuous UNSET borders should be activated.
                    _, _, countBlank = self.tools.getStatusCount(self.board, self.cellBorders[row][col])
                    if countBlank > 0:
                        for bdrIdx in contUnsetBdrs[0]:
                            if self.setBorder(bdrIdx, BorderStatus.ACTIVE):
                                self.displayMoveDesc(f'Activating continuous borders of 2-cell: {cellIdx}')
                                foundMove = True
                        for bdrIdx in self.board.tools.getCellBorders(row, col):
                            if bdrIdx not in contUnsetBdrs[0]:
                                if self.setBorder(bdrIdx, BorderStatus.BLANK):
                                    self.displayMoveDesc(f'Removing unset borders of solved 2-cell: {cellIdx}')
                                    foundMove = True
                    else:
                        topBdr, rightBdr, botBdr, leftBdr = self.board.tools.getCellBorders(row, col)

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
                            foundMove = foundMove | self.handleSmoothCorner(row, col, smoothDir)

        # Check every cell if it is poking a diagonally adjacent cell.
        pokeDirs = self.tools.getDirectionsCellIsPokingAt(self.board, row, col)
        for pokeDxn in pokeDirs:
            foundMove = foundMove | self.initiatePoke(row, col, pokeDxn)
        
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
                            self.displayMoveDesc(f'Activating continuous line: {borderIdx} to {connBdrIdx}')
                            return True

            connBdrTuple = self.board.tools.getConnectedBorders(borderIdx)

            _, countActive1, countBlank1 = self.tools.getStatusCount(self.board, connBdrTuple[0])
            _, countActive2, countBlank2 = self.tools.getStatusCount(self.board, connBdrTuple[1])

            if countActive1 > 1 or countActive2 > 1:
                if self.setBorder(borderIdx, BorderStatus.BLANK):
                    self.displayMoveDesc(f'Cleaning up active corner: {borderIdx}')
                    return True

            if countBlank1 == len(connBdrTuple[0]) or countBlank2 == len(connBdrTuple[1]):
                if self.setBorder(borderIdx, BorderStatus.BLANK):
                    self.displayMoveDesc(f'Cleaning up hanging border: {borderIdx}')
                    return True

        return foundMove

    def initiatePoke(self, origRow: int, origCol: int, dxn: DiagonalDirection) -> bool:
        """
        Initiate a poke on a diagonally adjacent cell from the origin cell.

        Arguments:
            origRow: The row index of the origin cell.
            origCol: The column index of the origin cell.
            dxn: The direction of the poke when it exits the origin cell.

        Returns:
            True if a move was found. False otherwise.
        """
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

        if self.board.tools.isValidCellIdx(targetRow, targetCol):
            return self.handleCellPoke(targetRow, targetCol, dxn.opposite())
        else:
            arms = self.board.tools.getArms(origRow, origCol, dxn)
            assert len(arms) < 2, f'Did not expect outer cell to have more than 1 arm. ' \
                f'Cell ({origRow}, {origCol}) has {len(arms)} arms at the {dxn} corner.'
            for bdrIdx in arms:
                # INVALID: If this arm right here is BLANK.
                if self.setBorder(bdrIdx, BorderStatus.ACTIVE):
                    self.displayMoveDesc(f'Activating an outer board border because of a poke: Cell {origRow}, {origCol}')
                    return True
        return False

    def handleCellPoke(self, row: int, col: int, dxn: DiagonalDirection, isExplicit: bool = False) -> bool:
        """
        Handle the situation when a cell is poked from a direction.
        The poke may or may not be explicit.

        An explicit poke is when there is exactly one `ACTIVE` arm and the rest are `BLANK`.

        Arguments:
            row: The row index of the poked cell.
            col: The column index of the poked cell.
            dxn: The direction of the poke when it enters the poked cell.
            isExplicit: True if the poke is explicit. Defaults to false.

        Returns:
            True if a move was found. False otherwise.
        """
        foundMove = False
        reqNum = self.board.cells[row][col]

        # If a cell is being poked at a particular corner and a border on that corner 
        # is already active, remove the other border on that corner.
        bdrIdx1, bdrIdx2 = self.board.tools.getCornerBorderIndices(row, col, dxn)
        bdrStat1 = self.board.borders[bdrIdx1]
        bdrStat2 = self.board.borders[bdrIdx2]
        if bdrStat1 == BorderStatus.ACTIVE:
            if self.setBorder(bdrIdx2, BorderStatus.BLANK):
                self.displayMoveDesc(f'Removing other border because cell is poked: Cell {row}, {col}')
                foundMove = True
        elif bdrStat2 == BorderStatus.ACTIVE:
            if self.setBorder(bdrIdx1, BorderStatus.BLANK):
                self.displayMoveDesc(f'Removing other border because cell is poked: Cell {row}, {col}')
                foundMove = True

        # If a 1-cell is poked, we know that its sole active border must be on that corner,
        # so we should remove the borders on the opposite corner.
        if reqNum == 1:
            blankBorders = self.board.tools.getCornerBorderIndices(row, col, dxn.opposite())
            # INVALID: If a the border opposite from the poke direction is already ACTIVE.
            for bdrIdx in blankBorders:
                if self.setBorder(bdrIdx, BorderStatus.BLANK):
                    self.displayMoveDesc(f'Removing borders away from poke direction of 1-cell: Cell {row}, {col}')
                    foundMove = True

        # If a 2-cell is poked, poke the cell opposite from the original poke direction.
        elif reqNum == 2:
            bdrIdx1, bdrIdx2 = self.board.tools.getCornerBorderIndices(row, col, dxn.opposite())
            # If 2-cell is poked, check if only one UNSET border is remaining on the opposite side.
            # If so, activate that border.
            if self.board.borders[bdrIdx1] == BorderStatus.BLANK:
                if self.setBorder(bdrIdx2, BorderStatus.ACTIVE):
                    self.displayMoveDesc(f'Activating remaining border on opposite side of poked 2-cell: Cell {row}, {col}')
                    foundMove = True
            elif self.board.borders[bdrIdx2] == BorderStatus.BLANK:
                if self.setBorder(bdrIdx1, BorderStatus.ACTIVE):
                    self.displayMoveDesc(f'Activating remaining border on opposite side of poked 2-cell: Cell {row}, {col}')
                    foundMove = True
            # Propagate the poke to the next cell
            self.initiatePoke(row, col, dxn.opposite())

        # If a 3-cell is poked, the borders opposite the poked corner should be activated.
        elif reqNum == 3:
            borders = self.board.tools.getCornerBorderIndices(row, col, dxn.opposite())
            for bdrIdx in borders:
                if self.setBorder(bdrIdx, BorderStatus.ACTIVE):
                    self.displayMoveDesc(f'Activating remaining border on opposite side of poked 2-cell: Cell {row}, {col}')
                    foundMove = True
            # Check if there is an active arm from the poke direction.
            # If there is, remove the other arms from that corner.
            arms = self.board.tools.getArms(row, col, dxn)
            armsStatuses = [self.board.borders[armIdx] for armIdx in arms]
            countUnset, countActive, _ = self.tools.getStatusCount(self.board, armsStatuses)
            # INVALID: If the number of active arms is more than 1
            if countActive == 1 and countUnset > 0:
                for bdrIdx in arms:
                    if self.board.borders[bdrIdx] == BorderStatus.UNSET:
                        if self.setBorder(bdrIdx, BorderStatus.BLANK):
                            self.displayMoveDesc(f'Removing unset arm of 3-cell where poke occurred: Cell {row}, {col}')
                            foundMove = True

        # As a general case, check if the poke should activate a lone border.
        bdrIdx1, bdrIdx2 = self.board.tools.getCornerBorderIndices(row, col, dxn)
        if self.board.borders[bdrIdx1] == BorderStatus.BLANK:
            if self.setBorder(bdrIdx2, BorderStatus.ACTIVE):
                # self.displayMoveDesc(f'Activating remaining border on opposite side of poked cell: Cell {row}, {col}')
                foundMove = True
        elif self.board.borders[bdrIdx2] == BorderStatus.BLANK:
            if self.setBorder(bdrIdx1, BorderStatus.ACTIVE):
                # self.displayMoveDesc(f'Activating remaining border on opposite side of poked cell: Cell {row}, {col}')
                foundMove = True

        return foundMove

    def handleSmoothCorner(self, row: int, col: int, dxn: DiagonalDirection) -> bool:
        """
        Handle the situation when a cell's corner is known to be smooth.

        A smooth corner is a corner where a poke will never occur.
        This means that this corner either has two `ACTIVE` borders or two `BLANK` borders.

        Arguments:
            row: The row index of the cell.
            col: The column index of the cell.
            dxn: The direction of the corner.

        Returns:
            True if a move was found. False otherwise.
        """
        moveFound = False
        reqNum = self.board.cells[row][col]

        cornerIdx1, cornerIdx2 = self.board.tools.getCornerBorderIndices(row, col, dxn)
        cornerStat1 = self.board.borders[cornerIdx1]
        cornerStat2 = self.board.borders[cornerIdx2]

        # If the borders are already both ACTIVE or both BLANK, then there is nothing to do here.
        if cornerStat1 == cornerStat2 and cornerStat1 != BorderStatus.UNSET:
            return False

        # If one border is UNSET and the other is either ACTIVE or BLANK, set it accordingly.
        if cornerStat1 != cornerStat2:
            if cornerStat1 == BorderStatus.UNSET:
                if self.setBorder(cornerIdx1, cornerStat2):
                    self.displayMoveDesc(f'Smoothing out corner {dxn}: Cell {row}, {col}')
                    return True
            elif cornerStat2 == BorderStatus.UNSET:
                if self.setBorder(cornerIdx2, cornerStat1):
                    self.displayMoveDesc(f'Smoothing out corner {dxn}: Cell {row}, {col}')
                    return True
            else:
                raise AssertionError(f'The cell {row},{col} should have a smooth {dxn} corner, ' \
                    'but its corners are invalid.')

        # A smooth corner on a 1-cell always means that both borders are BLANK.
        if reqNum == 1:
            for bdrIdx in (cornerIdx1, cornerIdx2):
                if self.setBorder(bdrIdx, BorderStatus.BLANK):
                    self.displayMoveDesc(f'Activating smooth corner {dxn} of 1-cell: Cell {row}, {col}')
                    moveFound = False
            return moveFound

        # A smooth corner on a 3-cell always means that both borders are ACTIVE.
        elif reqNum == 3:
            for bdrIdx in (cornerIdx1, cornerIdx2):
                if self.setBorder(bdrIdx, BorderStatus.ACTIVE):
                    self.displayMoveDesc(f'Activating smooth corner {dxn} of 3-cell: Cell {row}, {col}')
                    moveFound = False
            return moveFound

        elif reqNum == 2:
            # Initiate pokes on the directions where its corners isn't smooth.
            if dxn == DiagonalDirection.ULEFT or dxn == DiagonalDirection.LRIGHT:
                moveFound = moveFound | self.initiatePoke(row, col, DiagonalDirection.URIGHT)
                moveFound = moveFound | self.initiatePoke(row, col, DiagonalDirection.LLEFT)
            elif dxn == DiagonalDirection.URIGHT or dxn == DiagonalDirection.LLEFT:
                moveFound = moveFound | self.initiatePoke(row, col, DiagonalDirection.ULEFT)
                moveFound = moveFound | self.initiatePoke(row, col, DiagonalDirection.LRIGHT)
            else:
                raise ValueError(f'Invalid DiagonalDirection: {dxn}')
            
            # Propagate the smoothing because if a 2-cell's corner is smooth, the opposite corner is also smooth.
            targetCellIdx = self.board.tools.getCellIdxAtAdjCorner(row, col, dxn.opposite())
            if targetCellIdx is not None:
                targetRow, targetCol = targetCellIdx
                moveFound = moveFound | self.handleSmoothCorner(targetRow, targetCol, dxn)
        
        return False

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

    def displayMoveDesc(self, moveDesc: str) -> None:
        """
        Print the move description to the console.
        """
        # print(moveDesc)
