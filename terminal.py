import curses
from constants import DISPLAY_WIDTH
from objects import Hero, Enemy, PositionChange, StatusChange

from constants import Cell


cell_type_to_terminal_char = {
    Cell.EMPTY: " ",
    Cell.TANK: "T",
    Cell.ENEMY: "O",
    Cell.BULLET: "x",
    Cell.BRICKS: "B",
    Cell.IRON: "I",
}


class Terminal:
    def __init__(self):
        self._screen_obj = curses.initscr()
        self._screen_obj.nodelay(True)
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self._screen_obj.keypad(True)

        self.max_y, self.max_x = self.get_max_y_and_x()

    def get_max_y_and_x(self):
        max_y, max_x = self._screen_obj.getmaxyx()
        return max_y, int(max_x / 2)

    def get_pressed_key(self):
        return self._screen_obj.getch()

    def destroy(self, print_text_after_destroy: str = ""):
        curses.nocbreak()
        self._screen_obj.keypad(False)
        curses.echo()
        curses.endwin()

        if print_text_after_destroy:
            print(print_text_after_destroy)

    def print_changes(self, position_changes: list[PositionChange], status_chages: list[StatusChange]):
        for change in position_changes:
            char = cell_type_to_terminal_char[change.value]
            self._print(change.new_y, change.new_x * 2, char)
            if change.old_x:
                diff_x = change.new_x - change.old_x
                self._print(change.new_y, change.new_x * 2 - diff_x, char)

        for change in status_chages:
            if change.person_type == Hero:
                self._print_text(1, self.max_x * 2 - DISPLAY_WIDTH - 8, 'points:')
                self._print_number(1, self.max_x * 2 - DISPLAY_WIDTH, change.points)

        self._screen_obj.refresh()

    def _print(self, y: int, x: int, char: str):
        try:
            self._screen_obj.addch(y, x, char)
        except curses.error:
            pass

    def _print_text(self, y: int, x: int, text: str):
        for index, char in enumerate(text):
            self._print(y, x + index, char)

    def _print_number(self, y: int, x: int, number: int):
        self._print_text(y, x, str(number))
