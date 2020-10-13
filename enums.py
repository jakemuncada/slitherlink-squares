"""Contains the enums for this project."""

from enum import IntEnum


class BorderStatus(IntEnum):
    """
    The status of a Border. Can be `UNSET`, `ACTIVE`, or `BLANK`.

    `UNSET` is when the border is neither active nor blank.
    `ACTIVE` is when the border is a part of the cell border.
    `BLANK` is when the border is removed from the cell.
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
