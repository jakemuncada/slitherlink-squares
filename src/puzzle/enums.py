"""Contains the enums for this project."""

from __future__ import annotations
from enum import IntEnum
from typing import Optional, Tuple

OptInt = Optional[int]

Coord = Tuple[int, int]

class CardinalDirection(IntEnum):
    """
    The four cardinal directions: `TOP`, `RIGHT`, `BOT`, and `LEFT`.
    """
    TOP = 0
    RIGHT = 1
    BOT = 2
    LEFT = 3


class ExtendedDirection(IntEnum):
    """
    The four cardinal directions plus its diagonals.
    """
    TOP = 0
    URIGHT = 1
    RIGHT = 2
    LRIGHT = 3
    BOT = 4
    LLEFT = 5
    LEFT = 6
    ULEFT = 7

    def ceiling(self) -> ExtendedDirection:
        """
        Convert the direction to its top version.
        """
        if self == ExtendedDirection.LLEFT:
            return ExtendedDirection.ULEFT
        if self == ExtendedDirection.LRIGHT:
            return ExtendedDirection.URIGHT
        return self


class BorderStatus(IntEnum):
    """
    The status of a Border. Can be `UNSET`, `ACTIVE`, or `BLANK`.
    """
    UNSET = 0
    ACTIVE = 1
    BLANK = 2

    @classmethod
    def fromChar(cls, c):
        """Returns the equivalent BorderStatus of a given character."""
        return cls.fromInt(int(c))

    @classmethod
    def fromInt(cls, i):
        """Returns the equivalent BorderStatus of a given int."""
        if i == 0:
            return BorderStatus.UNSET
        if i == 1:
            return BorderStatus.ACTIVE
        if i == 2:
            return BorderStatus.BLANK
        raise AttributeError("Invalid BorderStatus value.")

    def __str__(self):
        if self == BorderStatus.UNSET:
            return "UNSET"
        if self == BorderStatus.ACTIVE:
            return "ACTIVE"
        if self == BorderStatus.BLANK:
            return "BLANK"
        raise AssertionError("Invalid Border Status")
