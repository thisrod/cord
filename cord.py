"""
Acme interface for Rope

Second goal: print every button-3 token in Python files.

Test routine: run this, open a Python file, type something, right click, check that the thing is written to stdout

TODO Clean up when Python windows are closed
"""

from asyncio import run, create_task
from asyncio.subprocess import create_subprocess_exec, PIPE

async def log_stream():
    return await nine_stream_for('acme/log')

async def nine_stream_for(path):
    process = await create_subprocess_exec('9p', 'read', path, stdout=PIPE, stderr=PIPE)
    return process.stdout


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
            event = await WindowEvent.scan(self.event_stream)
            print(F'Event for window {self.wid}: {event}', flush=True)
            # handle_event(txt.decode())


class WindowEvent():

    def __init__(self, origin, cause, start, end, flag, text):
        self.origin = origin
        self.cause = cause
        self.start = start
        self.end = end
        self.flag = flag
        self.text = text

    def __repr__(self):
        return (
            F'WindowEvent(origin={repr(self.origin)}, cause={repr(self.cause)}, '
            F'start={repr(self.start)}, end={repr(self.end)}, '
            F'flag={repr(self.flag)}, text={repr(self.text)})'
        )

    @classmethod
    async def scan(cls, aStream):
        s = await aStream.readline()
        s = s.decode()
        origin = s[0]
        cause = s[1]
        start, end, flag, length, text_line = s[2:].split(sep=' ', maxsplit=4)
        length = int(length)
        while len(text_line) < length+1:
            s = await aStream.readline()
            text_line += s.decode()
        assert text_line[length:] == '\n'
        return cls(origin, cause, int(start), int(end), int(flag), text_line[:length])


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