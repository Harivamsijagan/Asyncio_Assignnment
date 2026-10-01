## What is a coroutine?

A coroutine is a function (defined with `async def`) that can suspend its
execution at an `await` point and be resumed later from exactly where it
left off, with all its local state intact. Calling an `async def` function
doesn't run it — it produces a coroutine *object*, which is really a
special kind of generator that something else must drive forward.

## What is the difference between a coroutine and a Task?

A coroutine is just a paused/resumable computation — it does nothing on
its own. A Task is the thing that *owns and drives* a coroutine: it calls
`coroutine.send()`/`coroutine.throw()` to advance it, decides what to do
when the coroutine awaits something, and reschedules itself on the event
loop's ready queue. A coroutine is inert data; a Task is the active
scheduler-visible object wrapped around it.

## What does a Future represent?

A Future represents a value that doesn't exist yet but will (or an error
that will occur). It has two states, PENDING and DONE, and lets other code
register interest in "when this becomes available" via
`add_done_callback`, or simply `await` it directly.

## Why can a Task inherit from Future?

Because a Task's coroutine *itself* eventually produces a result (its
return value), a Task is naturally "a value that isn't ready yet." Making
`Task` a subclass of `Future` means a Task automatically gets `done()`,
`result()`, `add_done_callback()`, and — crucially — `__await__()` for
free, so one Task can `await` another Task exactly the same way it would
await any other Future.

## What happens when a Task starts executing a coroutine?

The Task calls `coroutine.send(None)` to start it. The coroutine body runs
synchronously until it hits an `await` on something not yet complete (or
finishes). Whatever that `await` ultimately yields propagates back up as
the return value of `send()`, which the Task inspects to decide what to do
next.

## What does `coroutine.send(None)` do?

It resumes (or starts) the coroutine, injecting `None` as the result of
whatever the coroutine is currently paused on (or, on the first call,
simply starts execution from the top). It runs the coroutine until the
next `await`/`yield` point or until it returns, at which point Python
raises `StopIteration` with the return value attached as `.value`.

## What happens internally when a coroutine executes `await future` and the Future is not complete?

`await future` calls `future.__await__()`, which is a generator. Since the
future isn't done, that generator executes `yield self` — i.e., it yields
the Future object itself. This yield propagates outward through every
enclosing `await` (Python chains `__await__` generators together) until it
reaches the top level of the coroutine that `coroutine.send()` is driving.
The Task sees this yielded Future, attaches a callback to it via
`add_done_callback`, and then stops calling `send()` — the coroutine is
now suspended in memory.

## How does completing a Future cause a suspended Task to resume?

When `future.set_result(value)` (or `set_exception`) runs, the Future
walks its list of registered callbacks and schedules each one with
`loop.call_soon(callback, self)`. The callback the Task registered
(`self._wakeup`) is one of these. When the event loop later pops that
callback off the ready queue and runs it, `_wakeup` reads the Future's
result and calls `self.step(value=result)`, which resumes the coroutine
with `coroutine.send(result)` — exactly the value that `await future`
should evaluate to.

## How does `await task` work if Task inherits from Future?

Identically to awaiting any Future: `Future.__await__` checks `done()`; if
not done, it yields the Task itself. The Task driving the *awaiting*
coroutine attaches a wakeup callback to the awaited Task via
`add_done_callback`. When the awaited Task's coroutine eventually returns,
`Task.step` catches the `StopIteration` and calls `self.set_result(...)`,
which — because Task is a Future — fires that callback and resumes the
awaiting Task with the returned value.

## Why is this scheduling model cooperative rather than preemptive?

There is no timer, signal, or OS thread interrupting a running coroutine.
A Task only ever pauses when its coroutine *itself* chooses to `await`
something (a Future, another Task, or `yield_control()`). Between those
points, a coroutine has exclusive, uninterrupted use of the interpreter.
Control only returns to the event loop when the coroutine voluntarily
gives it up — hence "cooperative."

## What happens if one coroutine performs a long-running computation without ever awaiting anything?

It blocks everything. Since nothing preempts a running coroutine, a
`coroutine.send()` call that never returns (because the coroutine body
never hits an `await`) will run to completion — or hang forever — before
the event loop gets to process any other Task or callback in the ready
queue. Cooperative scheduling only works if every coroutine awaits
regularly enough to give others a turn.