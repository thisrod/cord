"""
Acme interface for Rope

Second goal: print every button-3 token in Python files.

Test routine: run this, open a Python file, type something, right click, check that the thing is written to stdout

TODO Clean up when Python windows are closed
TODO make window and log events types of namedtuple
"""

import os
from asyncio import run, create_task
from asyncio.subprocess import create_subprocess_exec, PIPE
import subprocess

from rope.base.project import Project
from rope.contrib.findit import find_definition


async def nine_stream_for(path):
    process = await create_subprocess_exec("9p", "read", path, stdout=PIPE, stderr=PIPE)
    return process.stdout


def nine_file_content(path):
    process = subprocess.run(["9p", "read", path], text=True, capture_output=True)
    return process.stdout


def plumb(path, lineno):
    # Acme's address setting functions appear NYI
    process = subprocess.run(["plumb", f"{path}:{lineno}"])


class PythonWindow:
    def __init__(self, project, wid):
        self._wid = wid
        self.rope_module = project.find_module(self.path)
        self.project = project

    @property
    def stream(self):
        return EventStream(f"acme/{self.wid}/event", WindowEvent.scan, self)

    @property
    def wid(self):
        """Acme ID of the window"""
        return self._wid

    @property
    def path(self):
        """Path of the file"""
        tag = nine_file_content(f"acme/{self.wid}/tag")
        return tag.partition(" ")[0]

    @property
    def content(self):
        """The body text"""
        return nine_file_content(f"acme/{self.wid}/body")

    def handle_event(self, event):
        print(f"Event for window {self.wid}: {event}", flush=True)
        if event.is_look() and event.text:
            loc = find_definition(self.project, self.content, event.start - 1)


class WindowEvent:
    # TODO consider a named tuple and a scan function
    def __init__(self, origin, cause, start, end, flag, text):
        self.origin = origin
        self.cause = cause
        self.start = start
        self.end = end
        self.flag = flag
        self.text = text

    def is_look(self):
        return self.cause in "lL"

    def __repr__(self):
        return (
            f"WindowEvent(origin={repr(self.origin)}, cause={repr(self.cause)}, "
            f"start={repr(self.start)}, end={repr(self.end)}, "
            f"flag={repr(self.flag)}, text={repr(self.text)})"
        )

    @classmethod
    async def scan(cls, aStream):
        s = await aStream.readline()
        s = s.decode()
        origin = s[0]
        cause = s[1]
        start, end, flag, length, text_line = s[2:].split(sep=" ", maxsplit=4)
        length = int(length)
        while len(text_line) < length + 1:
            s = await aStream.readline()
            text_line += s.decode()
        assert text_line[length:] == "\n"
        return cls(origin, cause, int(start), int(end), int(flag), text_line[:length])


class TaskSet:
    """Record the scheduled tasks, and which windows they belong to"""

    def __init__(self):
        self._tasks = set()
        """(Window ID, task) pairs.  Wid is None for Editor tasks"""

    def run(self, wid, aCoroutine):
        self._tasks |= {(wid, create_task(aCoroutine))}


class EventStream:
    """Scan events, and pass them to a handler"""

    def __init__(self, path, scanner, handler):
        self.path = path
        self.scanner = scanner
        self.handler = handler

    async def handle_events(self):
        await self.open()
        while True:
            event = await self.scanner(self.stream)
            self.handler.handle_event(event)

    async def open(self):
        self.stream = await nine_stream_for(self.path)


async def scan_log_event(aStream):
    txt = await aStream.readline()
    return txt.decode().split()


class Editor:
    """
    An Acme instance with an associated rope project

    Responsible for handling top-level Acme events.  This needs
    access to the task set in order to cancel tasks for closed
    windows.
    """

    def __init__(self, event_tasks=TaskSet(), project=None, project_path=os.getcwd()):
        self._tasks = event_tasks
        if project is None:
            self.rope_project = Project(project_path)
        else:
            self.rope_project = project

    @property
    def stream(self):
        return EventStream("acme/log", scan_log_event, self)

    def handle_event(self, event):
        id, cmd, *name = event
        window = PythonWindow(self.rope_project, id)
        if cmd == "new" and name and name[0].endswith(".py"):
            self._tasks.run(id, window.stream.handle_events())
            print(f"Opened {name[0]} in window {window.wid}", flush=True)


async def main():
    editor = Editor()
    editor._tasks.run(None, editor.stream.handle_events())
    await next(x for x in editor._tasks._tasks)[1]


if __name__ == "__main__":
    run(main())
