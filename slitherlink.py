"""
This is the main entry point into the game.
"""

import sys
import pygame as pg

from src.main import main, test


if __name__ == '__main__':

    isTest = False

    for arg in sys.argv:
        if arg in ('-t', '--test'):
            isTest = True
    
    if isTest:
        test()
    else:
        main()
        pg.quit()
        sys.exit()