"""Pure-Python undo/redo history for thumbnail page order."""


class PageOrderHistory:
    def __init__(self):
        self.reset([])

    def reset(self, order):
        self._states = [tuple(order)]
        self._position = 0

    @property
    def current(self):
        return list(self._states[self._position])

    @property
    def can_undo(self):
        return self._position > 0

    @property
    def can_redo(self):
        return self._position + 1 < len(self._states)

    def record(self, order):
        state = tuple(order)
        if len(state) != len(self.current) or sorted(state) != sorted(self.current):
            raise ValueError("Page order must be a permutation of the original pages")
        if state == self._states[self._position]:
            return False
        self._states = self._states[:self._position + 1]
        self._states.append(state)
        self._position += 1
        return True

    def undo(self):
        if not self.can_undo:
            return self.current
        self._position -= 1
        return self.current

    def redo(self):
        if not self.can_redo:
            return self.current
        self._position += 1
        return self.current
