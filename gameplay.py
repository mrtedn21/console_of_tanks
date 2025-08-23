from random import randint
from typing import Optional
import logging

from game_field import GameField
from gameplay_utils import return_changes
from gameplay_exceptions import GameOverError
from constants import MotionDirection, Cell, ENEMIES_COUNT
from objects import BasePerson, Hero, Enemy, Bullet, PositionChange, StatusChange

logger = logging.getLogger()


class GamePlay:
    def __init__(self, max_height: int, max_width: int):
        self._game_field: GameField = GameField(max_height, max_width)
        self._bullets: list[Bullet] = []
        self._enemies: list[Enemy] = []
        self._hero: Hero = Hero(y=1, x=1)
        self._status_changes: list[StatusChange] = []

    @return_changes
    def init_map_and_heroes(self, game_map: list[list[int]]):
        for index_y, y in enumerate(game_map):
            for index_x, x in enumerate(y):
                self.update_cell(new_y=index_y, new_x=index_x, value=Cell(x))

        self.update_cell(new_y=self._hero.y, new_x=self._hero.x, value=Cell.TANK)
        for _ in range(ENEMIES_COUNT):
            enemy = self._get_new_enemy()
            self._enemies.append(enemy)
            self.update_cell(new_y=enemy.y, new_x=enemy.x, value=Cell.ENEMY)

        self.update_status(person_type=Hero, points=0)

    @return_changes
    def shoot(self, is_hero_shot: bool = False):
        if is_hero_shot:
            self._bullets.append(
                Bullet(
                    y=self._hero.y,
                    x=self._hero.x,
                    motion_direction=self._hero.motion_direction or MotionDirection.DOWN,
                    owner=Hero,
                )
            )

        for enemy in self._enemies:
            if self._is_random_allows_enemy_to_shoot() and enemy.lives_count:
                self._bullets.append(
                    Bullet(
                        y=enemy.y,
                        x=enemy.x,
                        motion_direction=enemy.motion_direction or MotionDirection(randint(1, 4)),
                        owner=Enemy,
                    )
                )

        for bullet in self._bullets:
            new_y, new_x = self._get_new_coordinate_by_motion_direction(
                bullet, bullet.motion_direction,
            )

            if self._game_field.get(new_y, new_x) == Cell.BRICKS:
                self._game_field.update_cells(
                    PositionChange(new_y=new_y, new_x=new_x, value=Cell.EMPTY),
                    PositionChange(new_y=bullet.y, new_x=bullet.x, value=Cell.EMPTY),
                )
                bullet.motion_direction = None

            elif (counter_enemy := self._get_enemy_by_coordinates(new_y, new_x)) and bullet.owner == Hero:
                counter_enemy.lives_count -= 1
                bullet.motion_direction = None
                counter_enemy.y, counter_enemy.x = self._get_random_coordinates()
                self._game_field.update_cells(
                    PositionChange(new_y=new_y, new_x=new_x, value=Cell.EMPTY),
                    PositionChange(new_y=bullet.y, new_x=bullet.x, value=Cell.EMPTY),
                    PositionChange(new_y=counter_enemy.y, new_x=counter_enemy.x, value=Cell.ENEMY),
                )
                self._hero.points += 1
                self.update_status(person_type=Hero, points=self._hero.points)

            elif self._game_field.get(new_y, new_x) == Cell.TANK:
                self._hero.lives_count -= 1
                self._hero.y, self._hero.x = 1, 1
                bullet.motion_direction = None
                self._game_field.update_cells(
                    PositionChange(new_y=new_y, new_x=new_x, value=Cell.EMPTY),
                    PositionChange(new_y=bullet.y, new_x=bullet.x, value=Cell.EMPTY),
                    PositionChange(new_y=1, new_x=1, value=Cell.TANK),
                )
                if not self._hero.lives_count:
                    raise GameOverError

            elif counter_bullet := self._get_bullet_by_coordinates(new_y, new_x):
                bullet.motion_direction = None
                counter_bullet.motion_direction = None
                self._game_field.update_cells(
                    PositionChange(
                        new_y=counter_bullet.y, new_x=counter_bullet.x, value=Cell.EMPTY
                    ),
                    PositionChange(new_y=bullet.y, new_x=bullet.x, value=Cell.EMPTY),
                )

            elif not self._can_object_move(new_y, new_x):
                bullet.motion_direction = None
                self.update_cell(new_y=bullet.y, new_x=bullet.x, value=Cell.EMPTY)

            else:
                self._game_field.update_cells(
                    PositionChange(new_y=new_y, new_x=new_x, value=Cell.BULLET),
                    PositionChange(new_y=bullet.y, new_x=bullet.x, value=Cell.EMPTY),
                )
                bullet.y, bullet.x = new_y, new_x

        self._bullets = [b for b in self._bullets if b.motion_direction]

        # This hack needs to rewrite Tank Cell if bullet writes to it. This is more pretty than
        # checking is new coordinates of bullet the same with tank, in reason of multiple checks
        for enemy in self._enemies:
            if enemy.lives_count:
                self.update_cell(new_y=enemy.y, new_x=enemy.x, value=Cell.ENEMY)
        if self._hero.lives_count:
            self.update_cell(new_y=self._hero.y, new_x=self._hero.x, value=Cell.TANK)

    @return_changes
    def move_hero(self, motion_direction: MotionDirection):
        if motion_direction == motion_direction.DO_NOTHING or not self._hero.lives_count:
            return

        self._hero.motion_direction = motion_direction
        new_y, new_x = self._get_new_coordinate_by_motion_direction(
            self._hero, motion_direction
        )

        if self._game_field.get(new_y, new_x) == Cell.ENEMY:
            self._hero.lives_count -= 1
            new_y, new_x = 1, 1
            self.update_cell(new_y=self._hero.y, new_x=self._hero.x, value=Cell.EMPTY)
            self.update_cell(new_y=1, new_x=1, value=Cell.TANK)
            if not self._hero.lives_count:
                raise GameOverError

        if not self._can_object_move(new_y, new_x):
            return

        self._game_field.update_cells(
            PositionChange(new_y=new_y, new_x=new_x, value=Cell.TANK),
            PositionChange(new_y=self._hero.y, new_x=self._hero.x, value=Cell.EMPTY),
        )
        self._hero.y, self._hero.x = new_y, new_x

    @return_changes
    def move_enemy(self):
        for enemy in self._enemies:
            if enemy.steps_count < 1:
                self._set_new_enemy_direction(enemy)

            new_y, new_x = self._get_new_coordinate_by_motion_direction(
                enemy, enemy.motion_direction
            )

            if self._game_field.get(new_y, new_x) == Cell.TANK:
                self._hero.lives_count -= 1
                self._hero.y, self._hero.x = 1, 1
                self.update_cell(new_y=self._hero.y, new_x=self._hero.x, value=Cell.EMPTY)
                self.update_cell(new_y=1, new_x=1, value=Cell.TANK)
                if not self._hero.lives_count:
                    raise GameOverError

            if not self._can_object_move(new_y, new_x):
                enemy.steps_count = 0
                return

            self._game_field.update_cells(
                PositionChange(new_y=enemy.y, new_x=enemy.x, value=Cell.EMPTY),
                PositionChange(new_y=new_y, new_x=new_x, value=Cell.ENEMY),
            )

            enemy.y = new_y
            enemy.x = new_x
            enemy.steps_count -= 1

    def _set_new_enemy_direction(self, enemy):
        enemy.steps_count = randint(2, self._game_field.height - 1)
        enemy.motion_direction = self._get_new_movement_direction(
            enemy.motion_direction,
        )

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
        new_dir = randint(1, 4)
        if new_dir == old_direction:
            return MotionDirection(self._get_new_movement_direction(new_dir))
        else:
            return MotionDirection(new_dir)

    def _can_object_move(self, new_y: int, new_x: int):
        return all(
            (
                0 <= new_y <= self._game_field.height - 1,
                0 <= new_x <= self._game_field.width - 1,
                self._game_field.get(new_y, new_x) != Cell.BRICKS,
            )
        )

    @staticmethod
    def _is_random_allows_enemy_to_shoot():
        """This functions detect random moment to allow enemy to shoot"""
        return randint(0, 30) == 0

    def _get_bullet_by_coordinates(self, y: int, x: int) -> Optional[Bullet]:
        return next(iter([b for b in self._bullets if (b.y, b.x) == (y, x)]), None)

    def _get_enemy_by_coordinates(self, y: int, x: int) -> Optional[Enemy]:
        return next(iter([e for e in self._enemies if (e.y, e.x) == (y, x)]), None)

    def _get_new_enemy(self):
        while True:
            y, x = self._get_random_coordinates()
            if self._game_field.get(y, x) != Cell.EMPTY:
                continue

            return Enemy(y=y, x=x)

    def _get_random_coordinates(self) -> tuple[int, int]:
        return randint(1, self._game_field.height - 1), randint(1, self._game_field.width - 1)

    def update_cell(self, new_y: int, new_x: int, value: Cell):
        self._game_field.update_cell(
            PositionChange(new_y=new_y, new_x=new_x, value=value)
        )

    def update_status(self, person_type: type[BasePerson], points: int):
        self._status_changes.append(StatusChange(person_type=person_type, points=points))

    def clear_changes(self):
        self._status_changes = []

    def get_changes(self):
        return self._status_changes
