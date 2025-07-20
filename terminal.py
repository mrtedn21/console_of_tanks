import curses
from constants import PositionChange

from gameplay_utils import Cell


cell_type_to_terminal_char = {
    Cell.EMPTY: " ",
    Cell.TRACK: "X",
    Cell.CONSIDER: " ",
    Cell.MARKED: "X",
    Cell.ENEMY: "O",
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

    def print_changes(self, changes: list[PositionChange]):
        for change in changes:
                char = cell_type_to_terminal_char[change.value]
                self._print(change.new_y, change.new_x * 2, char)
                if change.old_x:
                    diff_x = change.new_x - change.old_x
                    self._print(change.new_y, change.new_x * 2 - diff_x, char)
                elif change.value == Cell.MARKED:
                    self._print(change.new_y, change.new_x * 2 - 1, char)

        self._screen_obj.refresh()

    def _print(self, y, x, char):
        try:
            self._screen_obj.addch(y, x, char)
        except curses.error:
            pass
