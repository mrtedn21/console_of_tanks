from functools import cached_property
from constants import Cell, PositionChange
from typing import Optional


class GameField:
    def __init__(self, height: int, width: int):
        self._position_changes: list[PositionChange] = []
        self._matrix: list[list[Cell]] = [
            [Cell.EMPTY for _ in range(width)] for _ in range(height)
        ]

    def clear_changes(self):
        self._position_changes = []

    def get_changes(self):
        return self._position_changes

    def update_cell(self, position_change: PositionChange):
        try:
            self._matrix[position_change.new_y][position_change.new_x] = (
                position_change.value
            )
            self._position_changes.append(position_change)
        except IndexError:
            pass

    def update_cells(self, *position_changes: PositionChange):
        for position_change in position_changes:
            self.update_cell(position_change)

    def get(self, y: int, x: int) -> Optional[Cell]:
        try:
            return self._matrix[y][x]
        except IndexError:
            return None

    @cached_property
    def width(self) -> int:
        return len(self._matrix[0])

    @cached_property
    def height(self) -> int:
        return len(self._matrix)

    def __iter__(self):
        for i in self._matrix:
            for j in i:
                yield j
