import json
import asyncio
from collections import defaultdict

from gameplay import GamePlay
from gameplay_exceptions import GameOverError
from constants import MotionDirection
from terminal import Terminal
import logging

logging.basicConfig(filename='some.log', level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger()

global_pressed_key = None

ESCAPE_KEY = 27
SPACE = 32
UP_KEY = 259
DOWN_KEY = 258
LEFT_KEY = 260
RIGHT_KEY = 261


pressed_key_to_motion_direction = defaultdict(
    lambda: MotionDirection.DO_NOTHING,
    {
        UP_KEY: MotionDirection.UP,
        DOWN_KEY: MotionDirection.DOWN,
        LEFT_KEY: MotionDirection.LEFT,
        RIGHT_KEY: MotionDirection.RIGHT,
    },
)


async def shoot(terminal: Terminal, game_play):
    while global_pressed_key != ESCAPE_KEY:
        terminal.print_changes(*game_play.shoot(global_pressed_key == SPACE))
        await asyncio.sleep(1 / 50)


async def move_hero(terminal: Terminal, game_play):
    while global_pressed_key != ESCAPE_KEY:
        motion_direction = pressed_key_to_motion_direction[global_pressed_key]
        terminal.print_changes(*game_play.move_hero(motion_direction))
        await asyncio.sleep(1 / 50)


async def move_enemy(terminal: Terminal, game_play):
    while True:
        terminal.print_changes(*game_play.move_enemy())
        await asyncio.sleep(1 / 5)


async def reading_key(terminal: Terminal):
    global global_pressed_key
    while True:
        global_pressed_key = terminal.get_pressed_key()
        await asyncio.sleep(1 / 50)


async def main():
    terminal = Terminal()
    max_y, max_x = terminal.get_max_y_and_x()
    max_x -= 7

    with open('map.json') as f:
        game_map = json.load(f)

    game_play = GamePlay(max_y, max_x)

    terminal.print_changes(*game_play.init_map_and_heroes(game_map))

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(reading_key(terminal))
            tg.create_task(move_enemy(terminal, game_play))
            tg.create_task(shoot(terminal, game_play))
            tg.create_task(move_hero(terminal, game_play))

    except KeyboardInterrupt:
        terminal.destroy('Exit from game')
    except GameOverError:
        terminal.destroy('You lose, game over')
    finally:
        terminal.destroy()


if __name__ == '__main__':
    asyncio.run(main())
