"""
This is the main entry point into the game.
"""

import sys
import pygame as pg

from src.main import play, profile, test, testAll


def main():
    """Main function."""
    options = getOptions()
    loops = options['testloops']
    puzzleIndex = options['puzzleIndex']
    verbose = options['verbose']

    if options['profile']:
        profile(puzzleIndex)
    elif options['testall']:
        testAll(loops, verbose)
    elif options['test']:
        test(puzzleIndex, loops, verbose)
    else:
        play(puzzleIndex)
        pg.quit()
        sys.exit()


def getOptions() -> dict:
    """
    Get the run options from the command line arguments.
    """
    options = {}
    options['test'] = False
    options['testall'] = False
    options['profile'] = False
    options['testloops'] = None
    options['puzzleIndex'] = None
    options['verbose'] = None

    idx = 1
    while idx < len(sys.argv):
        if sys.argv[idx] in ('-t', '--test'):
            options['test'] = True
        elif sys.argv[idx] in ('--testall',):
            options['testall'] = True
        elif sys.argv[idx] in ('-p', '--profile'):
            options['profile'] = True
        elif sys.argv[idx] in ('-v', '--verbose'):
            options['verbose'] = True
        else:
            if sys.argv[idx] in ('-l', '--loops') and idx + 1 < len(sys.argv):
                options['testloops'] = int(sys.argv[idx + 1])
            elif sys.argv[idx] in ('-i', '--index') and idx + 1 < len(sys.argv):
                options['puzzleIndex'] = int(sys.argv[idx + 1])
            idx += 1
        idx += 1

    return options


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
