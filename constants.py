from dataclasses import dataclass
from typing import Optional
from enum import Enum

ENEMIES_COUNT = 2
DISPLAY_WIDTH = 10


class MotionDirection(int, Enum):
    UP = 1
    DOWN = 2
    RIGHT = 3
    LEFT = 4
    DO_NOTHING = 5


class Cell(Enum):
    """This class presents cell on game field.
    Empty cell means usual cell. In start of
    game all cells are empty. Track cell means
    temp marked. Cell become track when game
    person move, behind him remains track of
    marked cells. But if enemy will cross over
    the track, game person lose and die, and
    track cells became again empty. Last type
    is marked, cell becomes marked when person
    successfully moves from one border to anoter
    and all shape that drawed by track becomes
    marked, forever"""

    EMPTY = 0
    ENEMY = 1
    TANK = 2
    BULLET = 3
    BRICKS = 4
    IRON = 5

@dataclass
class BaseGamePlayChange:
    pass


@dataclass
class PositionChange(BaseGamePlayChange):
    new_y: int
    new_x: int

    value: Cell

    old_y: Optional[int] = None
    old_x: Optional[int] = None


@dataclass
class StatusChange(BaseGamePlayChange):
    hero_points: int = 0
