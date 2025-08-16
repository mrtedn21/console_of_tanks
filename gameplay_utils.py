def return_changes(func):
    def foo(self, *args, **kwargs):
        self._game_field.clear_changes()
        self.clear_changes()

        func(self, *args, **kwargs)

        position_changes = self._game_field.get_changes()
        status_changes = self.get_changes()

        return position_changes, status_changes

    return foo
