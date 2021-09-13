"""
This is the main entry point into the game.
"""

import sys
import pygame as pg

from src.main import main


if __name__ == '__main__':
    main()
    pg.quit()
    sys.exit()