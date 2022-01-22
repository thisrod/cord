"""
Acme interface for Rope

Initial goal: print a message when a Python file is opened.
"""

from subprocess import Popen, PIPE, DEVNULL, run

window_events = Popen(['9p', 'read', 'acme/log'], bufsize=0, text=True, stdout=PIPE, stderr=PIPE)
print('Started', flush=True)
while True:
    wid, cmd, *name = window_events.stdout.readline().split()
    if cmd == 'new' and name and name[0].endswith('.py'):
       print(F'Opened {name[0]} in window {wid}', flush=True)
