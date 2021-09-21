"""
This module contains the renderer class
which draws the current puzzle state onto the screen.
"""

from functools import cache
from typing import Any, Optional

import pygame as pg
from pygame.rect import Rect
from pygame.surface import Surface

from src.point import Point
from src.puzzle.board import Board
from src.puzzle.board_tools import BoardTools
from src.puzzle.enums import BorderStatus, CardinalDirection, DiagonalDirection

pg.init()
pg.display.set_caption('Slitherlink Squares')

SCREEN_SIZE = (1200, 980)
SCREEN_RECT = pg.Rect((0, 0), SCREEN_SIZE)
SCREEN_MARGIN = (20, 10, 20, 10)  # left, top, right, bot
RECT_MARGIN = 4
PUZZ_RECT = pg.Rect(SCREEN_MARGIN[0], SCREEN_MARGIN[1],
                    SCREEN_SIZE[0] - (SCREEN_MARGIN[0] + SCREEN_MARGIN[2]),
                    SCREEN_SIZE[1] - (SCREEN_MARGIN[1] + SCREEN_MARGIN[3]))
SCREEN_CENTER = (SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2)

COLORKEY = (255, 0, 255)
BG_COLOR = (7, 8, 9)
BORDER_UNSET_COLOR = (120, 120, 120)
VERTEX_COLOR = (255, 255, 255)
CELL_LABEL_COLOR = (255, 255, 255)

BORDER_ACTIVE_THICKNESS = 3
BORDER_UNSET_THICKNESS = 2
BORDER_BLANK_THICKNESS = 2
BORDER_DASH_LENGTH = 5
VERTEX_RADIUS = 2

CELL_FONT = pg.font.SysFont("Courier", 20)


class Renderer:
    """
    The renderer class which draws the current puzzle state onto the screen.
    """

    def __init__(self, board: Board) -> None:
        self.board = board
        self.screen: Surface = pg.display.set_mode(SCREEN_SIZE)
        self.baseSurface: Surface = pg.Surface((PUZZ_RECT.width, PUZZ_RECT.height))
        self.vtxSurface: Surface = pg.Surface((PUZZ_RECT.width, PUZZ_RECT.height))
        self.cellLabelSurface: Surface = pg.Surface((PUZZ_RECT.width, PUZZ_RECT.height))
        self.borderSurface: Surface = pg.Surface((PUZZ_RECT.width, PUZZ_RECT.height))
        self.cellGroupOverlay: Surface = pg.Surface((PUZZ_RECT.width, PUZZ_RECT.height))

        self.showCellGroupOverlay = False

        # Compute the optimal cell size
        totalWidth = PUZZ_RECT.width - (RECT_MARGIN * 2)
        totalHeight = PUZZ_RECT.height - (RECT_MARGIN * 2)
        cellWidth = totalWidth // self.board.cols
        cellHeight = totalHeight // self.board.rows
        sz = min(cellWidth, cellHeight)
        self.cellSize = (sz, sz)

        actualWidth = self.board.cols * sz
        actualHeight = self.board.rows * sz

        PUZZ_RECT.left = (SCREEN_SIZE[0] - actualWidth) // 2
        PUZZ_RECT.top = (SCREEN_SIZE[1] - actualHeight) // 3

        self.prepare()
        self.draw()

    def toggleCellGroupOverlay(self) -> None:
        """
        Show/hide the cell group overlay.
        """
        self.showCellGroupOverlay = not self.showCellGroupOverlay

    def prepare(self) -> None:
        """
        Prepare the surfaces based on the size of the board.
        """
        def _drawDashedLine(pt1, pt2):
            point1 = (pt1[0], pt1[1])
            point2 = (pt2[0], pt2[1])
            self.drawDashedLine(self.baseSurface, BORDER_UNSET_COLOR,
                                point1, point2, BORDER_UNSET_THICKNESS)

        def _drawVtx(pt):
            pg.draw.circle(self.vtxSurface, VERTEX_COLOR, pt, VERTEX_RADIUS)

        def _drawLabel(pt, num):
            if num is not None:
                self.drawText(self.cellLabelSurface, str(num), (pt[0] + 1, pt[1] + 2), CELL_FONT, CELL_LABEL_COLOR)

        self.baseSurface.set_colorkey(COLORKEY)
        self.baseSurface.fill(COLORKEY)

        self.vtxSurface.set_colorkey(COLORKEY)
        self.vtxSurface.fill(COLORKEY)

        self.cellLabelSurface.set_colorkey(BG_COLOR)
        self.cellLabelSurface.fill(BG_COLOR)

        self.borderSurface.set_colorkey(COLORKEY)
        self.cellGroupOverlay.set_colorkey(COLORKEY)

        for i in range(self.board.rows):
            for j in range(self.board.cols):
                ul = self.getVertexCoords(i, j, DiagonalDirection.ULEFT)
                ur = self.getVertexCoords(i, j, DiagonalDirection.URIGHT)
                ll = self.getVertexCoords(i, j, DiagonalDirection.LLEFT)
                lr = self.getVertexCoords(i, j, DiagonalDirection.LRIGHT)
                center = self.getCellCoords(i, j)
                _drawDashedLine(ul, ur)
                _drawDashedLine(ul, ll)
                _drawDashedLine(ur, lr)
                _drawDashedLine(ll, lr)
                _drawVtx(ul)
                _drawVtx(ur)
                _drawVtx(ll)
                _drawVtx(lr)
                _drawLabel(center, self.board.cells[i][j])

    def draw(self) -> None:
        """
        Draw the given board onto the screen.
        """
        self.screen.fill(BG_COLOR)
        self.screen.blit(self.baseSurface, PUZZ_RECT)

        if self.showCellGroupOverlay:
            self.updateCellGroupOverlay()
            self.screen.blit(self.cellGroupOverlay, PUZZ_RECT)

        self.screen.blit(self.cellLabelSurface, PUZZ_RECT)
        self.drawBorders()
        self.screen.blit(self.borderSurface, PUZZ_RECT)
        self.screen.blit(self.vtxSurface, PUZZ_RECT)
        pg.display.update()

    def drawBorders(self) -> None:
        """
        Draw the `BLANK` and `ACTIVE` borders of the board.
        """
        self.borderSurface.fill(COLORKEY)
        doneBorders: set[int] = set()

        def _drawBorder(row, col, direction):
            bdrIdx = BoardTools.getBorderIdx(row, col, direction)
            if bdrIdx not in doneBorders:
                doneBorders.add(bdrIdx)
                status = self.board.borders[bdrIdx]
                if status in (BorderStatus.ACTIVE, BorderStatus.BLANK):
                    if direction == CardinalDirection.TOP:
                        v1 = self.getVertexCoords(i, j, DiagonalDirection.ULEFT)
                        v2 = self.getVertexCoords(i, j, DiagonalDirection.URIGHT)
                    elif direction == CardinalDirection.RIGHT:
                        v1 = self.getVertexCoords(i, j, DiagonalDirection.URIGHT)
                        v2 = self.getVertexCoords(i, j, DiagonalDirection.LRIGHT)
                    elif direction == CardinalDirection.BOT:
                        v1 = self.getVertexCoords(i, j, DiagonalDirection.LLEFT)
                        v2 = self.getVertexCoords(i, j, DiagonalDirection.LRIGHT)
                    elif direction == CardinalDirection.LEFT:
                        v1 = self.getVertexCoords(i, j, DiagonalDirection.ULEFT)
                        v2 = self.getVertexCoords(i, j, DiagonalDirection.LLEFT)
                    else:
                        raise ValueError(f'Invalid direction: {direction}')

                    if status == BorderStatus.ACTIVE:
                        pg.draw.line(self.borderSurface, (255, 30, 30), v1, v2, BORDER_ACTIVE_THICKNESS)
                    else:
                        pg.draw.line(self.borderSurface, BG_COLOR, v1, v2, BORDER_ACTIVE_THICKNESS)

        for i in range(self.board.rows):
            for j in range(self.board.cols):
                _drawBorder(i, j, CardinalDirection.RIGHT)
                _drawBorder(i, j, CardinalDirection.BOT)
                if i == 0:
                    _drawBorder(i, j, CardinalDirection.TOP)
                if j == 0:
                    _drawBorder(i, j, CardinalDirection.LEFT)

    def updateCellGroupOverlay(self) -> None:
        """
        Update the cell group overlay surface.
        """
        self.cellGroupOverlay.fill(COLORKEY)

        colors = [(0, 0, 120), (0, 120, 0)]

        for row in range(self.board.rows):
            for col in range(self.board.cols):
                colorIdx = self.board.cellGroups[row][col]
                if colorIdx is not None:
                    ul = self.getVertexCoords(row, col, DiagonalDirection.ULEFT)
                    lr = self.getVertexCoords(row, col, DiagonalDirection.LRIGHT)

                    margin = 3
                    left = ul[0] + (margin * 1.5)
                    top = ul[1] + (margin * 1.5)
                    width = lr[0] - ul[0] - (margin * 2)
                    height = lr[1] - ul[1] - (margin * 2)

                    color = colors[colorIdx]
                    rect = Rect(left, top, width, height)
                    pg.draw.rect(self.cellGroupOverlay, color, rect)

    def drawDashedLine(self, surface: Surface, color: tuple[int, int, int],
                       pt1: tuple[int, int], pt2: tuple[int, int], thickness: int) -> Rect:
        """
        Draw a dashed line.

        Arguments:
            surface: The surface to draw on.
            color: The line color.
            pt1: The coordinates of one endpoint.
            pt2: The coordinates of the other endpoint.
            thickness: The thickness of the dashed line.

        Returns:
            The rect of the dashed line.
        """
        origin = Point(pt1)
        target = Point(pt2)
        displacement = target - origin
        length = len(displacement)
        slope = Point((displacement.x / length, displacement.y / length))

        # Draw the dashes
        for index in range(0, length // BORDER_DASH_LENGTH, 2):
            start = origin + (slope * index * BORDER_DASH_LENGTH)
            end = origin + (slope * (index + 1) * BORDER_DASH_LENGTH)
            pg.draw.line(surface, color, start.get(), end.get(), thickness)

    def drawText(self, surface: pg.Surface, text: str, coords: Point, font: Any,
                 color: tuple[int, int, int]) -> Rect:
        """
        Draw the text on the given surface.

        Arguments:
            surface: The surface to draw on.
            text: The text to display.
            coords: The center coordinates of the text rect.
            font: The font to be used.
            color: The text color.

        Returns:
            The rect of the drawn text.
        """
        fontSurface = font.render(str(text), False, color, BG_COLOR)
        rect = fontSurface.get_rect(center=coords)
        surface.blit(fontSurface, rect)
        return rect

    @cache
    def getVertexCoords(self, row: int, col: int, direction: DiagonalDirection) -> tuple[int, int]:
        """
        Get the screen coordinates of the cell's vertex in the given direction.
        The upperleft-most vertex is always at coordinate (0, 0).

        Arguments:
            row: The target cell's row index.
            col: The target cell's column index.
            direction: The direction of the vertex. Must be ULEFT, URIGHT, LLEFT, or LRIGHT.

        Returns:
            The vertex's screen coordinates.
        """
        if direction in (DiagonalDirection.ULEFT, DiagonalDirection.URIGHT):
            x = col * self.cellSize[0]
            x += self.cellSize[0] if direction == DiagonalDirection.URIGHT else 0
            y = row * self.cellSize[1]
        elif direction in (DiagonalDirection.LLEFT, DiagonalDirection.LRIGHT):
            if row < self.board.rows - 1:
                return self.getVertexCoords(row + 1, col, direction.ceiling())
            x = col * self.cellSize[0]
            x += self.cellSize[0] if direction == DiagonalDirection.LRIGHT else 0
            y = (row * self.cellSize[1]) + self.cellSize[1]
        else:
            raise ValueError

        return (x + RECT_MARGIN, y + RECT_MARGIN)

    @cache
    def getBorderCoords(self, row: int, col: int, direction: CardinalDirection) -> tuple[int, int]:
        """
        Get the midpoint coordinates of the target border.

        Arguments:
            row: The target cell's row index.
            col: The target cell's column index.
            direction: The direction of the target border.

        Returns:
            The target border's screen coordinates.
        """
        halfWidth = self.cellSize[0] // 2
        halfHeight = self.cellSize[1] // 2
        cellCoords = self.getCellCoords(row, col)
        if direction == CardinalDirection.TOP:
            x = cellCoords[0]
            y = cellCoords[1] - halfHeight
        elif direction == CardinalDirection.RIGHT:
            x = cellCoords[0] + halfWidth
            y = cellCoords[1]
        elif direction == CardinalDirection.BOT:
            x = cellCoords[0]
            y = cellCoords[1] + halfHeight
        elif direction == CardinalDirection.LEFT:
            x = cellCoords[0] - halfWidth
            y = cellCoords[1]
        else:
            raise ValueError(f'Invalid direction: {direction}')
        return (x, y)

    @cache
    def getCellCoords(self, row: int, col: int) -> tuple[int, int]:
        """
        Get the screen coordinates of the cell center.

        Arguments:
            row: The target cell's row index.
            col: The target cell's column index.

        Returns:
            The cell's screen coordinates.
        """
        x = (col * self.cellSize[0]) + (self.cellSize[0] // 2)
        y = (row * self.cellSize[1]) + (self.cellSize[1] // 2)
        return (x + RECT_MARGIN, y + RECT_MARGIN)

    def getClosestCell(self, pt: Point) -> Optional[tuple[int, int]]:
        """
        Get the index of the cell that is closest to the given coordinates.

        Arguments:
            pt: The given point.

        Returns:
            The index of the closest cell. Returns None if there is no cell close by.
        """
        adjX = pt.x - PUZZ_RECT.left
        adjY = pt.y - PUZZ_RECT.top
        pt = Point((adjX, adjY))

        refDist = min(self.cellSize[0], self.cellSize[1])
        minDist = 999999
        closestIdx = None
        for i in range(self.board.rows):
            for j in range(self.board.cols):
                coords = self.getCellCoords(i, j)
                dist = pt.dist(Point(coords))
                if dist < refDist and dist < minDist:
                    minDist = dist
                    closestIdx = (i, j)
        return closestIdx

    def getClosestBorderIdx(self, pt: Point, closestCell: Optional[tuple[int, int]] = None) -> Optional[int]:
        """
        Get the index of the border that is closest to the given coordinates.

        Arguments:
            pt: The given point.

        Returns:
            The index of the closest border. Returns None if there is no border close by.
        """
        adjX = pt.x - PUZZ_RECT.left
        adjY = pt.y - PUZZ_RECT.top
        pt = Point((adjX, adjY))

        refDist = min(self.cellSize[0] // 2, self.cellSize[1] // 2)
        minDist = 999999
        closestIdx = None
        if closestCell is None:
            for i in range(self.board.rows):
                for j in range(self.board.cols):
                    for direction in CardinalDirection:
                        coords = self.getBorderCoords(i, j, direction)
                        borderPt = Point(coords)
                        dist = pt.dist(borderPt)
                        if dist < refDist and dist < minDist:
                            minDist = dist
                            closestIdx = BoardTools.getBorderIdx(i, j, direction)
        else:
            for direction in CardinalDirection:
                coords = self.getBorderCoords(closestCell[0], closestCell[1], direction)
                borderPt = Point(coords)
                dist = pt.dist(borderPt)
                if dist < refDist and dist < minDist:
                    minDist = dist
                    closestIdx = BoardTools.getBorderIdx(closestCell[0], closestCell[1], direction)
        return closestIdx
