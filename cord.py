"""
Acme interface for Rope

Second goal: print every button-3 token in Python files.

TODO Clean up when Python windows are closed
"""

# from subprocess import Popen, PIPE, DEVNULL
from asyncio import run, wait, create_task, FIRST_COMPLETED
from asyncio.subprocess import create_subprocess_exec, PIPE

async def line_reader(aStream):
    return aStream, await aStream.readline()

async def event_stream_for(s):
    events = await create_subprocess_exec('9p', 'read', F'acme/{s}', stdout=PIPE, stderr=PIPE)
    return events.stdout

async def main():
    window_stream = await event_stream_for('log')
    print('Started', flush=True)
    while True:
        done, pending = await wait([line_reader(window_stream)], return_when=FIRST_COMPLETED)
        x, txt = await next(t for t in done)
        assert x == window_stream
        wid, cmd, *name = txt.decode().split()
        if cmd == 'new' and name and name[0].endswith('.py'):
           print(F'Opened {name[0]} in window {wid}', flush=True)

run(main())