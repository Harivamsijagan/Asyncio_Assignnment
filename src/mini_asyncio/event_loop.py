from collections import deque
from .task import Task

class EventLoop:

    def __init__(self):
        self.ready = deque()
        self._running = False

    def call_soon(self, callback, *args):
        self.ready.append((callback, args))

    def create_task(self, coroutine):
        return Task(coroutine, self)

    def run_forever(self):
        self._running = True
        while self._running and self.ready:
            callback, args = self.ready.popleft()
            callback(*args)
        self._running = False

    def run_until_complete(self, task):
        task.add_done_callback(lambda _future: self.stop())
        self.run_forever()
        return task.result()

    def stop(self):
        self._running = False