"""
Acme interface for Rope

Second goal: print every button-3 token in Python files.

Test routine: run this, open a Python file, type something, right click, check that the thing is written to stdout

TODO Write a proper event reader, that accepts newlines in the text field
TODO Clean up when Python windows are closed
"""

from asyncio import run, create_task, FIRST_COMPLETED
from asyncio.subprocess import create_subprocess_exec, PIPE

async def log_stream():
    return await nine_stream_for('acme/log')

async def nine_stream_for(path):
    process = await create_subprocess_exec('9p', 'read', path, stdout=PIPE, stderr=PIPE)
    return process.stdout

def handle_event(s):
    origin = s[0]
    cause = s[1]
    start, end, flag, length, *text = s[2:].split()
    if cause == 'L':
        print(origin, cause, start, end, flag, length, text, flush=True)

class PythonWindow():
    def __init__(self, wid):
        self._wid = wid

    @property
    def wid(self):
        """Acme ID of the window"""
        return self._wid

    async def open_event_stream(self):
        self.event_stream = await nine_stream_for(F'acme/{self.wid}/event')

    async def handle_events(self):
        await self.open_event_stream()
        while True:
            txt = await self.event_stream.readline()
            print(F'Event for window {self.wid}: {txt.decode()}', flush=True)
            # handle_event(txt.decode())


class WindowEvent():
    pass


async def main():
    event_tasks = set()
    window_stream = await log_stream()
    print('Started', flush=True)
    while True:
        txt = await window_stream.readline()
        id, cmd, *name = txt.decode().split()
        window = PythonWindow(id)
        if cmd == 'new' and name and name[0].endswith('.py'):
            event_tasks |= {create_task(window.handle_events())}
            print(F'Opened {name[0]} in window {window.wid}', flush=True)

if __name__ == '__main__':
    run(main())