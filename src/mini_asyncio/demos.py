import os
import sys


if __package__ in (None, ""):
    package_parent = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    sys.path.insert(0, package_parent)

from mini_asyncio import EventLoop, Future, yield_control



def demo_1():
    print("--- Demo 1: single coroutine ---")
    loop = EventLoop()

    async def hello():
        print("hello")
        return 42

    task = loop.create_task(hello())
    result = loop.run_until_complete(task)

    print(result)


def demo_2():
    print("--- Demo 2: two cooperative tasks ---")
    loop = EventLoop()

    async def worker(name):
        print(name, "start")
        await yield_control()
        print(name, "end")

    loop.create_task(worker("A"))
    loop.create_task(worker("B"))
    loop.run_forever()


def demo_3():
    print("--- Demo 3: multiple yields ---")
    loop = EventLoop()

    async def worker(name):
        print(name, 1)
        await yield_control()
        print(name, 2)
        await yield_control()
        print(name, 3)

    loop.create_task(worker("A"))
    loop.create_task(worker("B"))
    loop.run_forever()


def demo_4():
    print("--- Demo 4: awaiting a Future ---")
    loop = EventLoop()
    future = Future(loop)

    async def waiter():
        print("waiting")
        result = await future
        print(result)

    loop.create_task(waiter())
    loop.call_soon(future.set_result, "done")
    loop.run_forever()


def demo_5():
    print("--- Demo 5: awaiting another Task ---")
    loop = EventLoop()

    async def calculate():
        await yield_control()
        return 100

    async def main():
        task = loop.create_task(calculate())
        result = await task
        return result

    main_task = loop.create_task(main())
    result = loop.run_until_complete(main_task)
    print(result)


if __name__ == "__main__":
    demo_1()
    demo_2()
    demo_3()
    demo_4()
    demo_5()