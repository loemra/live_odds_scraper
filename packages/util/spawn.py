import asyncio

_background_tasks = set()


def spawn(coro):
    task = asyncio.create_task(coro)

    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
