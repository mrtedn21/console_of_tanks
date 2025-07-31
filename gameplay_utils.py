def return_changes(func):
    def foo(self, *args, **kwargs):
        self._game_field.clear_changes()
        func(self, *args, **kwargs)
        return self._game_field.get_changes()

    return foo
