class InvalidStateError(Exception):
    pass


class Future:
    def __init__(self, loop):
        self.loop = loop
        self._done = False
        self._result = None
        self._exception = None
        self._callbacks = []

    def done(self):
        return self._done

    def result(self):
        if not self._done:
            raise InvalidStateError("Future is not done yet")
        if self._exception is not None:
            raise self._exception
        return self._result

    def set_result(self, value):
        if self._done:
            raise InvalidStateError("Future result already set")
        self._result = value
        self._done = True
        self._schedule_callbacks()

    def set_exception(self, exc):
        if self._done:
            raise InvalidStateError("Future result already set")
        self._exception = exc
        self._done = True
        self._schedule_callbacks()

    def add_done_callback(self, callback):
        # If already done, schedule the callback right away (but still via
        # call_soon, never invoke it synchronously -- keeps behavior
        # consistent whether the Future was already complete or not).
        if self._done:
            self.loop.call_soon(callback, self)
        else:
            self._callbacks.append(callback)

    def _schedule_callbacks(self):
        callbacks, self._callbacks = self._callbacks, []
        for cb in callbacks:
            self.loop.call_soon(cb, self)

    def __await__(self):
        # If already complete, no need to suspend at all.
        if not self._done:
            # Yielding `self` bubbles up through every enclosing `await`
            # until it reaches the Task driving the top-level coroutine.
            yield self
        return self.result()