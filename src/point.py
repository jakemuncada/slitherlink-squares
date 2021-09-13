"""
A coordinate point class.
"""

from math import sqrt


class Point:
    """A coordinate point class."""

    def __init__(self, pt=(0, 0)):
        self.x = float(pt[0])
        self.y = float(pt[1])

    def __add__(self, other):
        return Point((self.x + other.x, self.y + other.y))

    def __sub__(self, other):
        return Point((self.x - other.x, self.y - other.y))

    def __mul__(self, scalar):
        return Point((self.x * scalar, self.y * scalar))

    def __div__(self, scalar):
        return Point((self.x / scalar, self.y / scalar))

    def __len__(self):
        return int(sqrt(self.x * self.x + self.y * self.y))

    def __str__(self):
        return '{:.2f}, {:.2f}'.format(self.x, self.y)

    def dist(self, other) -> float:
        """Get distance to another point."""
        return sqrt((self.x - other.x) * (self.x - other.x) +
                    (self.y - other.y) * (self.y - other.y))

    def get(self) -> tuple[int, int]:
        """Returns the x and y coordinate as a tuple of ints."""
        return (int(self.x), int(self.y))
