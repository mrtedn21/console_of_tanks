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
        self._screen_obj.keypad(True)

        self.max_y, self.max_x = self.get_max_y_and_x()

    def get_max_y_and_x(self):
        return self._screen_obj.getmaxyx()

    def get_pressed_key(self):
        return self._screen_obj.getch()

    def destroy(self, print_text_after_destroy: str = ""):
        curses.nocbreak()
        self._screen_obj.keypad(False)
        curses.echo()
        curses.endwin()

        if print_text_after_destroy:
            print(print_text_after_destroy)

    #def print_changes(self, changes: list[PositionChange]):
    #    for change in changes:
    #        if change.new_cell == Cell.BORDER:
    #            self._print_border(change.new_y, change.new_x)
    #        else:
    #            char = cell_type_to_terminal_char[change.new_cell]
    #            self._print(change.new_y, change.new_x * 2, char)

    #            if change.old_y:
    #                char = cell_type_to_terminal_char[change.old_cell]
    #                self._print(change.old_y, change.old_x, char)
    #            else:
    #                self._print(change.new_y, change.new_x , char)

    #    self._screen_obj.refresh()

    def print_changes(self, changes: list[PositionChange]):
        for change in changes:
            if change.new_cell == Cell.BORDER:
                self._print_border(change.new_y, change.new_x)
            elif change.new_cell == Cell.TRACK:
                char = cell_type_to_terminal_char[change.new_cell]
                self._print(change.new_y, change.new_x * 2, char)
                if change.new_y == change.old_y:
                    self._print(change.new_y, change.new_x * 2 - 1, char)
            elif change.new_cell == Cell.MARKED:
                char = cell_type_to_terminal_char[change.new_cell]
                self._print(change.new_y, change.new_x * 2, 'w')
                self._print(change.new_y, change.new_x * 2 - 1, 'w')
            else:
                char = cell_type_to_terminal_char[change.new_cell]
                self._print(change.new_y, change.new_x, char)

        self._screen_obj.refresh()

    def _print(self, y, x, char):
        try:
            self._screen_obj.addch(y, x, char)
        except curses.error:
            pass

    def _print_border(self, y: int, x: int):
        if y == self.max_y - 1 and x == self.max_x - 1:
            self._print(y, x * 2, "┘")

        elif y == 0 and x == 0:
            self._print(y, x * 2, "┌")

        elif y == self.max_y - 1 and x == 0:
            self._print(y, x * 2, "└")

        elif y == 0 and x == self.max_x - 1:
            self._print(y, x * 2, "┐")

        elif y == 0 or y == self.max_y - 1:
            self._print(y, x * 2, "─")
            self._print(y, x * 2 - 1, "─")

        elif x == 0 or x == self.max_x - 1:
            self._print(y, x * 2, "│")
