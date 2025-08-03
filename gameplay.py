from typing import Optional
from dataclasses import dataclass
import random
import logging

from game_field import GameField
from constants import Cell
from gameplay_utils import return_changes
from constants import MotionDirection, PositionChange

logger = logging.getLogger()


@dataclass
class BasePerson:
    y: int
    x: int
    motion_direction: Optional[MotionDirection] = None


@dataclass
class Hero(BasePerson):
    pass


@dataclass
class Bullet(BasePerson):
    pass


@dataclass
class Enemy(BasePerson):
    steps_count: Optional[int] = None


class GamePlay:
    def __init__(self, max_height: int, max_width: int):
        self._game_field: GameField = GameField(max_height, max_width)
        self._hero = Hero(y=1, x=1)
        self._bullets: list[Bullet] = []
        self._enemy = Enemy(
            y=int(self._game_field.height / 2),
            x=int(self._game_field.width / 2),
            steps_count=0,
            motion_direction=None,
        )

    @return_changes
    def init_map_and_heroes(self, game_map: list[list[int]]):
        for index_y, y in enumerate(game_map):
            for index_x, x in enumerate(y):
                self._game_field.update_cell(
                    PositionChange(new_y=index_y, new_x=index_x, value=Cell(x))
                )
        self._game_field.update_cells(
            PositionChange(new_y=self._hero.y, new_x=self._hero.x, value=Cell.TANK),
            PositionChange(new_y=self._enemy.y, new_x=self._enemy.x, value=Cell.ENEMY),
        )

    @return_changes
    def shoot(self, is_hero_shot: False):
        if not self._hero.motion_direction:
            self._hero.motion_direction = MotionDirection.DOWN

        if is_hero_shot:
            self._bullets.append(Bullet(
                y=self._hero.y, x=self._hero.x,
                motion_direction=self._hero.motion_direction,
            ))

        for bullet in self._bullets:
            new_y, new_x = (
                self._get_new_coordinate_by_motion_direction(bullet, bullet.motion_direction)
            )

            if self._game_field.get(new_y, new_x) == Cell.BRICKS:
                self._game_field.update_cells(
                    PositionChange(new_y=new_y, new_x=new_x, value=Cell.EMPTY),
                    PositionChange(new_y=bullet.y, new_x=bullet.x, value=Cell.EMPTY),
                )
                bullet.motion_direction = None
            elif not self._can_object_move(new_y, new_x):
                bullet.motion_direction = None
                self._game_field.update_cell(
                    PositionChange(new_y=bullet.y, new_x=bullet.x, value=Cell.EMPTY),
                )
            else:
                self._game_field.update_cells(
                    PositionChange(new_y=new_y, new_x=new_x, value=Cell.BULLET),
                    PositionChange(new_y=bullet.y, new_x=bullet.x, value=Cell.EMPTY),
                )
                bullet.y, bullet.x = new_y, new_x

        self._bullets = [b for b in self._bullets if b.motion_direction]

        # This hack needs to rewrite Tank Cell if bullet writes to it. This is more pretty than
        # checking is new coordinates of bullet the same with tank, in reason of multiple checks
        self._game_field.update_cell(
            PositionChange(new_y=self._hero.y, new_x=self._hero.x, value=Cell.TANK),
        )

    @return_changes
    def move_hero(self, motion_direction: MotionDirection):
        if motion_direction == motion_direction.DO_NOTHING:
            return

        self._hero.motion_direction = motion_direction
        new_hero_y, new_hero_x = (
            self._get_new_coordinate_by_motion_direction(self._hero, motion_direction)
        )

        if not self._can_object_move(new_hero_y, new_hero_x):
            return

        self._game_field.update_cells(
            PositionChange(new_y=new_hero_y, new_x=new_hero_x, value=Cell.TANK),
            PositionChange(new_y=self._hero.y, new_x=self._hero.x, value=Cell.EMPTY),
        )
        self._hero.y, self._hero.x = new_hero_y, new_hero_x

    @return_changes
    def move_enemy(self):
        if self._enemy.steps_count < 1:
            self._set_new_enemy_direction()

        new_enemy_y, new_enemy_x = (
            self._get_new_coordinate_by_motion_direction(self._enemy, self._enemy.motion_direction)
        )

        if not self._can_object_move(new_enemy_y, new_enemy_x):
            self._enemy.steps_count = 0
            return

        self._game_field.update_cells(
            PositionChange(new_y=self._enemy.y, new_x=self._enemy.x, value=Cell.EMPTY),
            PositionChange(new_y=new_enemy_y, new_x=new_enemy_x, value=Cell.ENEMY),
        )

        self._enemy.y = new_enemy_y
        self._enemy.x = new_enemy_x
        self._enemy.steps_count -= 1

    def _set_new_enemy_direction(self):
        self._enemy.steps_count = random.randint(2, self._game_field.height - 1)
        self._enemy.motion_direction = self._get_new_movement_direction(
            self._enemy.motion_direction,
        )

    def _is_coordinates_of_tank(self, y: int, x: int):
        return self._hero.y == y and self._hero.x == x

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
        if foo := decision_mapping.get(motion_direction):
            return foo(some_person.y, some_person.x)
        else:
            return some_person.y, some_person.x

    def _get_new_movement_direction(self, old_direction):
        new_dir = random.randint(1, 4)
        if new_dir == old_direction:
            return MotionDirection(self._get_new_movement_direction(new_dir))
        else:
            return MotionDirection(new_dir)

    def _can_object_move(self, new_y: int, new_x: int):
        return all((
            0 <= new_y <= self._game_field.height - 1,
            0 <= new_x <= self._game_field.width - 1,
            self._game_field.get(new_y, new_x) == Cell.EMPTY,
        ))
