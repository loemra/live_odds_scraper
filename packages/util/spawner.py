import asyncio


background_tasks = set()

def spawn(awaitable):
    t = asyncio.create_task(awaitable)
    background_tasks.add(t)
    t.add_done_callback(background_tasks.discard)
