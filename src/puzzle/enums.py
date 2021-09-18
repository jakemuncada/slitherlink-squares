"""Contains the enums for this project."""

from __future__ import annotations
from enum import IntEnum
from typing import Optional, Tuple


OptInt = Optional[int]

Coord = Tuple[int, int]


class InvalidBoardException(Exception):
    pass


class CardinalDirection(IntEnum):
    """
    The four cardinal directions: `TOP`, `RIGHT`, `BOT`, and `LEFT`.
    """
    TOP = 0
    RIGHT = 1
    BOT = 2
    LEFT = 3


class DiagonalDirection(IntEnum):
    """
    The four diagonal directions: `ULEFT`, `URIGHT`, `LRIGHT`, and `LLEFT`.
    """
    ULEFT = 0
    URIGHT = 1
    LRIGHT = 2
    LLEFT = 3

    def opposite(self) -> DiagonalDirection:
        """
        Returns the opposite direction.
        """
        if self == DiagonalDirection.URIGHT:
            return DiagonalDirection.LLEFT
        elif self == DiagonalDirection.LRIGHT:
            return DiagonalDirection.ULEFT
        elif self == DiagonalDirection.LLEFT:
            return DiagonalDirection.URIGHT
        elif self == DiagonalDirection.ULEFT:
            return DiagonalDirection.LRIGHT

    def ceiling(self) -> DiagonalDirection:
        """
        Convert the direction to its top version.
        """
        if self == DiagonalDirection.LLEFT:
            return DiagonalDirection.ULEFT
        if self == DiagonalDirection.LRIGHT:
            return DiagonalDirection.URIGHT
        return self

    def __str__(self) -> str:
        if self == DiagonalDirection.URIGHT:
            return "URIGHT"
        elif self == DiagonalDirection.LRIGHT:
            return "LRIGHT"
        elif self == DiagonalDirection.LLEFT:
            return "LLEFT"
        elif self == DiagonalDirection.ULEFT:
            return "ULEFT"


class BorderStatus(IntEnum):
    """
    The status of a Border. Can be `UNSET`, `ACTIVE`, or `BLANK`.
    """
    UNSET = 0
    ACTIVE = 1
    BLANK = 2

    def opposite(self):
        """
        Get the opposite border status.
        """
        if self == BorderStatus.ACTIVE:
            return BorderStatus.BLANK
        elif self == BorderStatus.BLANK:
            return BorderStatus.ACTIVE
        raise ValueError('Only ACTIVE and BLANK statuses have an opposite.')

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
        raise ValueError("Invalid BorderStatus value.")

    def __str__(self):
        if self == BorderStatus.UNSET:
            return "UNSET"
        if self == BorderStatus.ACTIVE:
            return "ACTIVE"
        if self == BorderStatus.BLANK:
            return "BLANK"
        raise ValueError("Invalid Border Status")


class CornerEntry(IntEnum):
    """
    The type of corner of the cell based on how many arms
    it is supposed to have.
    """
    POKE = 0
    SMOOTH = 1
    UNKNOWN = 2

    def opposite(self) -> CornerEntry:
        """Returns the opposite CornerEntry."""
        if self == CornerEntry.POKE:
            return CornerEntry.SMOOTH
        if self == CornerEntry.SMOOTH:
            return CornerEntry.POKE
        raise ValueError("Only POKE and SMOOTH corner entries have opposites.")

    def __str__(self) -> str:
        if self == CornerEntry.POKE:
            return "POKE"
        if self == CornerEntry.SMOOTH:
            return "SMOOTH"
        if self == CornerEntry.UNKNOWN:
            return "UNKNOWN"
        raise ValueError("Invalid CornerEntry")
