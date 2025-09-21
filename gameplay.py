from pickle import OBJ
from posix import remove
from random import randint
import logging

from game_field import GameField
from gameplay_utils import return_changes
from gameplay_exceptions import GameOverError
from constants import MotionDirection, Cell, ENEMIES_COUNT
from objects import (
    BasePerson,
    Hero,
    Enemy,
    Bullet,
    PositionChange,
    BaseStatusChange,
    PointsStatusChange,
    LivesStatusChange,
    PersonToCellMap,
)

logger = logging.getLogger()


class GamePlay:
    def __init__(self, max_height: int, max_width: int):
        self._game_field: GameField = GameField(max_height, max_width)
        self._bullets: list[Bullet] = []
        self._enemies: list[Enemy] = []
        self._hero: Hero = Hero(y=1, x=1)
        self._status_changes: list[BaseStatusChange] = []

    @return_changes
    def init_map_and_heroes(self, game_map: list[list[int]]):
        for index_y, y in enumerate(game_map):
            for index_x, x in enumerate(y):
                self.update(new_y=index_y, new_x=index_x, value=Cell(x))

        self.update(object=self._hero)
        for _ in range(ENEMIES_COUNT):
            new_enemy_y, new_enemy_x = self._get_random_coordinates_for_enemy()
            enemy = Enemy(y=new_enemy_y, x=new_enemy_x)
            self._enemies.append(enemy)
            self.update(object=enemy)

        self.update_points_status(person_type=Hero, value=0)
        self.update_lives_status(person_type=Hero, value=self._hero.lives_count)

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
                bullet,
                bullet.motion_direction,
            )

            if self._game_field.get(new_y, new_x) == Cell.BRICKS:
                self.update(new_y=new_y, new_x=new_x, value=Cell.EMPTY)
                self.update(object=bullet, remove_object=True)

            elif (
                counter_enemy := self._get_enemy_by_coordinates(new_y, new_x)
            ) and bullet.owner == Hero:
                counter_enemy.lives_count -= 1
                counter_enemy.y, counter_enemy.x = self._get_random_coordinates_for_enemy()
                self.update(new_y=new_y, new_x=new_x, value=Cell.EMPTY)
                self.update(object=bullet, remove_object=True)
                self.update(object=counter_enemy)
                self._hero.points += 1
                self.update_points_status(person_type=Hero, value=self._hero.points)

            elif self._game_field.get(new_y, new_x) == Cell.TANK and Bullet.owner == Hero:
                self._hero.lives_count -= 1
                self.update(new_y=new_y, new_x=new_x, value=Cell.EMPTY)
                self.update(object=bullet, remove_object=True)
                self.update(object=self._hero, new_y=1, new_x=1)
                self.update_lives_status(person_type=Hero, value=self._hero.lives_count)
                if not self._hero.lives_count:
                    raise GameOverError

            elif counter_bullet := self._get_bullet_by_coordinates(new_y, new_x):
                bullet.motion_direction = None
                counter_bullet.motion_direction = None
                self.update(object=counter_bullet, remove_object=True)
                self.update(object=bullet, remove_object=True)

            elif not self._can_object_move(new_y, new_x):
                self.update(object=bullet, remove_object=True)

            else:
                self.update(object=bullet, remove_object=True)
                self.update(object=bullet, new_y=new_y, new_x=new_x)

        self._bullets = [b for b in self._bullets if b.motion_direction]

        # This hack needs to rewrite Tank Cell if bullet writes to it. This is more pretty than
        # checking is new coordinates of bullet the same with tank, in reason of multiple checks
        for enemy in self._enemies:
            if enemy.lives_count:
                self.update(object=enemy)
        if self._hero.lives_count:
            self.update(self._hero)

    @return_changes
    def move_hero(self, motion_direction: MotionDirection):
        if motion_direction == motion_direction.DO_NOTHING or not self._hero.lives_count:
            return

        self._hero.motion_direction = motion_direction
        new_y, new_x = self._get_new_coordinate_by_motion_direction(self._hero, motion_direction)

        if self._game_field.get(new_y, new_x) == Cell.ENEMY:
            self.update(object=self._hero, remove_object=True)
            self.update(object=self._hero, new_y=1, new_x=1)
            self.update_lives_status(person_type=Hero, value=self._hero.lives_count)
            if not self._hero.lives_count:
                raise GameOverError

        elif not self._can_object_move(new_y, new_x):
            return

        else:
            self.update(object=self._hero, clear_object=True)
            self.update(object=self._hero, new_y=new_y, new_x=new_x)

    @return_changes
    def move_enemy(self):
        for enemy in self._enemies:
            if enemy.steps_count < 1:
                self._set_new_enemy_direction(enemy)

            new_y, new_x = self._get_new_coordinate_by_motion_direction(
                enemy, enemy.motion_direction
            )

            if self._game_field.get(new_y, new_x) == Cell.TANK:
                self.update(object=self._hero, remove_object=True)
                self.update(object=self._hero, new_y=1, new_x=1)
                self.update_lives_status(person_type=Hero, value=self._hero.lives_count)
                if not self._hero.lives_count:
                    raise GameOverError

            if not self._can_object_move(new_y, new_x):
                enemy.steps_count = 0
                return

            self.update(object=enemy, clear_object=True)
            self.update(object=enemy, new_y=new_y, new_x=new_x)

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
                self._game_field.get(new_y, new_x) not in (Cell.BRICKS, Cell.IRON),
            )
        )

    @staticmethod
    def _is_random_allows_enemy_to_shoot():
        """This functions detect random moment to allow enemy to shoot"""
        return randint(0, 30) == 0

    def _get_bullet_by_coordinates(self, y: int, x: int) -> Bullet | None:
        return next(iter([b for b in self._bullets if (b.y, b.x) == (y, x)]), None)

    def _get_enemy_by_coordinates(self, y: int, x: int) -> Enemy | None:
        return next(iter([e for e in self._enemies if (e.y, e.x) == (y, x)]), None)

    def _get_random_coordinates_for_enemy(self) -> tuple[int, int]:
        while True:
            y = randint(1, self._game_field.height - 1)
            x = randint(1, self._game_field.width - 1)

            if self._game_field.get(y, x) != Cell.EMPTY:
                continue

            diff_with_hero = abs(y - self._hero.y) + abs(x - self._hero.x)
            if diff_with_hero < 10:
                continue

            return y, x

    def update(
        self,
        object: BasePerson | None = None,
        new_y: int | None = None,
        new_x: int | None = None,
        value: Cell | None = None,
        remove_object: bool = False,
        clear_object: bool = False,
    ):
        if object and value is None:
            object.y, object.x = new_y, new_x
            value = PersonToCellMap[type(object)]

        if new_y is None and new_x is None:
            # In this case game play needs to use current coordinates of object
            new_y, new_x = object.y, object.x

        if remove_object or clear_object:
            value = Cell.EMPTY

        if remove_object:
            if isinstance(object, Bullet):
                object.motion_direction = None
            elif isinstance(object, Hero):
                object.lives_count -= 1

        self._game_field.update_cell(PositionChange(new_y=new_y, new_x=new_x, value=value))

    def update_points_status(self, person_type: type[BasePerson], value: int):
        self._status_changes.append(PointsStatusChange(person_type=person_type, value=value))

    def update_lives_status(self, person_type: type[BasePerson], value: int):
        self._status_changes.append(LivesStatusChange(person_type=person_type, value=value))

    def clear_changes(self):
        self._status_changes = []

    def get_changes(self):
        return self._status_changes
