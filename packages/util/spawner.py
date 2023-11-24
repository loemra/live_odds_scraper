import asyncio

__background_tasks = set()


def spawn(awaitable):
    t = asyncio.create_task(awaitable)
    __background_tasks.add(t)
    t.add_done_callback(__background_tasks.discard)
