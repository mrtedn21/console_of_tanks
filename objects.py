from dataclasses import dataclass
from typing import Optional
from constants import MotionDirection, Cell


@dataclass
class BasePerson:
    y: int
    x: int
    motion_direction: Optional[MotionDirection] = None
    points: int = 0
    lives_count: int = 3


@dataclass
class Hero(BasePerson):
    pass


@dataclass
class Enemy(BasePerson):
    steps_count: int = 0


@dataclass
class Bullet(BasePerson):
    owner: Optional[type[Hero | Enemy]] = None


@dataclass
class PositionChange:
    new_y: int
    new_x: int

    value: Cell

    old_y: Optional[int] = None
    old_x: Optional[int] = None


@dataclass
class BaseStatusChange:
    person_type: type[BasePerson]
    value: int


@dataclass
class PointsStatusChange(BaseStatusChange):
    pass


@dataclass
class LivesStatusChange(BaseStatusChange):
    pass
