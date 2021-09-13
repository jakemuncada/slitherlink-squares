"""
This module contains the control class for the entire game.
"""

from src.puzzle.enums import BorderStatus
from typing import Optional
import pygame as pg
from pygame.display import update
from pygame.time import Clock

from .puzzle.board import Board
from .render import Renderer
from .point import Point

FPS = 30
TIME_PER_UPDATE = 1000.0 / FPS


class Control:
    """
    The control class for the entire game.
    Contains the game loop and the event_loop.
    """

    def __init__(self, board: Board) -> None:
        self.board = board
        self.done = False
        self.clock: Clock = pg.time.Clock()
        self.renderer = Renderer(board)

    def start(self) -> None:
        """
        Start the rendering.
        """
        self.renderer.draw()
        lag = 0.0
        while not self.done:
            lag += self.clock.tick(FPS)
            self.event_loop()
            while lag >= TIME_PER_UPDATE:
                lag -= TIME_PER_UPDATE

    def event_loop(self) -> None:
        """
        Process all events.
        """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            elif event.type == pg.KEYDOWN:
                self.keys = pg.key.get_pressed()
                self.renderer.draw()
            elif event.type == pg.MOUSEBUTTONDOWN:
                mouseX, mouseY = pg.mouse.get_pos()
                closestCell = self.renderer.getClosestCell(Point((mouseX, mouseY)))
                borderIdx = self.renderer.getClosestBorderIdx(Point((mouseX, mouseY)), closestCell)
                if pg.mouse.get_pressed() == (True, False, False):
                    # Left Click
                    self.clickBorder(borderIdx)
                elif pg.mouse.get_pressed() == (False, False, True):
                    # Right Click
                    self.clickCell(closestCell)

    def clickBorder(self, borderIdx: Optional[int]) -> None:
        """
        Handle the border click.

        Arguments:
            borderIdx: The index of the clicked border.
        """
        if borderIdx is not None:
            if self.board.borders[borderIdx] == BorderStatus.UNSET:
                self.board.borders[borderIdx] = BorderStatus.ACTIVE
            elif self.board.borders[borderIdx] == BorderStatus.ACTIVE:
                self.board.borders[borderIdx] = BorderStatus.BLANK
            elif self.board.borders[borderIdx] == BorderStatus.BLANK:
                self.board.borders[borderIdx] = BorderStatus.UNSET
            self.renderer.draw()

    def clickCell(self, cellIdx: Optional[tuple[int, int]]) -> None:
        """
        Handle the cell click.

        Arguments:
            borderIdx: The index of the clicked border.
        """