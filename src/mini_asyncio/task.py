
from .future import Future


class Task(Future):
   

    def __init__(self, coroutine, loop):
        super().__init__(loop)
        self.coroutine = coroutine
        # Schedule the very first step instead of running immediately,
        # so create_task() never blocks the caller.
        self.loop.call_soon(self.step)

    def step(self, value=None, exc=None):
        try:
            if exc is not None:
                yielded = self.coroutine.throw(type(exc), exc, exc.__traceback__)
            else:
                yielded = self.coroutine.send(value)

        except StopIteration as stop:
            # The coroutine returned -- capture its final value.
            self.set_result(stop.value)
            return

        except Exception as error:  # noqa: BLE001 - propagate as Task's own error
            self.set_exception(error)
            return

        # The coroutine is still running; look at what it yielded.
        if yielded is None:
            # await yield_control() -- just go to the back of the queue.
            self.loop.call_soon(self.step)
        elif isinstance(yielded, Future):
            # await some_future / await some_other_task
            yielded.add_done_callback(self._wakeup)
        else:
            raise RuntimeError(
                f"Task received unsupported yield value: {yielded!r}"
            )

    def _wakeup(self, future):
        try:
            result = future.result()
        except Exception as error:  # noqa: BLE001
            self.step(exc=error)
        else:
            self.step(value=result)