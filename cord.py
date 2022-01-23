"""
Acme interface for Rope

Second goal: print every button-3 token in Python files.

TODO Write a proper event reader, that accepts newlines in the text field
TODO Clean up when Python windows are closed
"""

from asyncio import run, create_task, FIRST_COMPLETED
from asyncio.subprocess import create_subprocess_exec, PIPE

async def log_stream():
    events = await nine_stream_for('acme/log')
    return events.stdout

async def event_stream_for(wid):
    events = await nine_stream_for(F'acme/{wid}/event')
    return events.stdout

async def nine_stream_for(path):
    return await create_subprocess_exec('9p', 'read', path, stdout=PIPE, stderr=PIPE)

async def handle_events(wid):
    event_stream = await event_stream_for(wid)
    while True:
        txt = await event_stream.readline()
        print(F'Event for window {wid}: {txt.decode()}', flush=True)
        # handle_event(txt.decode())

def handle_event(s):
    origin = s[0]
    cause = s[1]
    start, end, flag, length, *text = s[2:].split()
    if cause == 'L':
        print(origin, cause, start, end, flag, length, text, flush=True)

async def main():
    event_tasks = set()
    window_stream = await log_stream()
    print('Started', flush=True)
    while True:
        txt = await window_stream.readline()
        wid, cmd, *name = txt.decode().split()
        if cmd == 'new' and name and name[0].endswith('.py'):
            event_tasks |= {create_task(handle_events(wid))}
            print(F'Opened {name[0]} in window {wid}', flush=True)

run(main())