from typing import Optional
from dataclasses import dataclass
import random

from game_field import GameField
from gameplay_utils import Cell
from gameplay_exceptions import GameOverError, GameWinError
from gameplay_utils import LittleFigureDetector, return_changes
from constants import MotionDirection, PositionChange


@dataclass
class BasePerson:
    y: int
    x: int


@dataclass
class Hero(BasePerson):
    pass


@dataclass
class Enemy(BasePerson):
    steps_count: int
    motion_direction: Optional[MotionDirection] = None


class GamePlay:
    def __init__(self, max_height: int, max_width: int):
        self._game_field: GameField = GameField(max_height, max_width)
        self._hero = Hero(y=1, x=1)
        self._enemy = Enemy(
            y=int(self._game_field.height / 2),
            x=int(self._game_field.width / 2),
            steps_count=0,
            motion_direction=None,
        )

    @return_changes
    def init_borders_on_game_field(self):
        for i in range(self._game_field.height):
            self._game_field.update_cells(
                PositionChange(new_y=i, new_x=0, new_cell=Cell.BORDER),
                PositionChange(new_y=i, new_x=self._game_field.width - 1, new_cell=Cell.BORDER),
            )

        for j in range(self._game_field.width):
            self._game_field.update_cells(
                PositionChange(new_y=0, new_x=j, new_cell=Cell.BORDER),
                PositionChange(new_y=self._game_field.height - 1, new_x=j, new_cell=Cell.BORDER),
            )

    @return_changes
    def init_enemy_and_hero_on_game_field(self):
        self._game_field.update_cells(
            PositionChange(new_y=self._hero.y, new_x=self._hero.x, new_cell=Cell.TRACK),
            PositionChange(new_y=self._enemy.y, new_x=self._enemy.x, new_cell=Cell.ENEMY),
        )

    @return_changes
    def make_progress(self, hero_motion_direction: MotionDirection):
        self._move_hero(hero_motion_direction)
        self._move_enemy()

    def _move_hero(self, motion_direction: MotionDirection):
        if motion_direction == motion_direction.DO_NOTHING:
            return

        new_hero_y, new_hero_x = (
            self._get_new_coordinate_by_motion_direction(self._hero, motion_direction)
        )

        if self._is_border_reached(new_hero_y, new_hero_x):
            LittleFigureDetector(self._game_field).detect()
            if self._is_enemy_lose():
                raise GameWinError

        if not self._can_person_go(new_hero_y, new_hero_x):
            return

        self._game_field.update_cell(
            PositionChange(new_y=new_hero_y, new_x=new_hero_x, new_cell=Cell.TRACK,
                           old_y=self._hero.y, old_x=self._hero.x, old_cell=Cell.EMPTY,
        ))
        self._hero.y, self._hero.x = new_hero_y, new_hero_x

    def _move_enemy(self):
        if self._enemy.steps_count < 1:
            self._set_new_enemy_direction()

        new_enemy_y, new_enemy_x = (
            self._get_new_coordinate_by_motion_direction(self._enemy, self._enemy.motion_direction)
        )

        if self._is_enemy_reached_track(new_enemy_y, new_enemy_x):
            raise GameOverError

        if not self._can_person_go(new_enemy_y, new_enemy_x):
            self._set_new_enemy_direction()
            return

        #self._game_field.update_cell(PositionChange(
        #    old_y=self._enemy.y, old_x=self._enemy.x, old_cell=Cell.EMPTY,
        #    new_y=new_enemy_y, new_x=new_enemy_x, new_cell=Cell.ENEMY,
        #))
        self._game_field.update_cells(
            PositionChange(new_y=self._enemy.y, new_x=self._enemy.x, new_cell=Cell.EMPTY),
            PositionChange(new_y=new_enemy_y, new_x=new_enemy_x, new_cell=Cell.ENEMY),
        )

        self._enemy.y, self._enemy.x = new_enemy_y, new_enemy_x
        self._enemy.steps_count -= 1

    def _set_new_enemy_direction(self):
        self._enemy.steps_count = random.randint(2, self._game_field.height - 1)
        self._enemy.motion_direction = self._get_new_movement_direction(
            self._enemy.motion_direction,
        )

    def _can_person_go(self, new_y: int, new_x: int) -> bool:
        return self._game_field.get(new_y, new_x) == Cell.EMPTY

    def _is_enemy_reached_track(self, new_y: int, new_x: int) -> bool:
        return self._game_field.get(new_y, new_x) == Cell.TRACK

    def _is_border_reached(self, new_y: int, new_x: int) -> bool:
        return self._game_field.get(new_y, new_x) in (Cell.BORDER, Cell.MARKED)

    def _is_on_track(self, new_y: int, new_x: int) -> bool:
        return self._game_field.get(new_y, new_x) == Cell.TRACK

    def _is_enemy_lose(self):
        return all((
            self._game_field.get(self._enemy.y + 1, self._enemy.x) in (Cell.BORDER, Cell.MARKED),
            self._game_field.get(self._enemy.y - 1, self._enemy.x) in (Cell.BORDER, Cell.MARKED),
            self._game_field.get(self._enemy.y, self._enemy.x - 1) in (Cell.BORDER, Cell.MARKED),
            self._game_field.get(self._enemy.y, self._enemy.x + 1) in (Cell.BORDER, Cell.MARKED),
        ))

    @staticmethod
    def _get_new_coordinate_by_motion_direction(
        some_person: BasePerson, motion_direction: MotionDirection
    ) -> tuple[int, int]:
        decision_mapping = {
            MotionDirection.UP: lambda y, x: (y - 1, x),
            MotionDirection.DOWN: lambda y, x: (y + 1, x),
            MotionDirection.RIGHT: lambda y, x: (y, x + 1),
            MotionDirection.LEFT: lambda y, x: (y, x - 1),
        }
        return decision_mapping[motion_direction](some_person.y, some_person.x)

    def _get_new_movement_direction(self, old_direction):
        new_dir = random.randint(1, 4)
        if new_dir == old_direction:
            return MotionDirection(self._get_new_movement_direction(new_dir))
        else:
            return MotionDirection(new_dir)
