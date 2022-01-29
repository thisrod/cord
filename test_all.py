from unittest import TestCase
from io import BytesIO
import asyncio

from cord import WindowEvent

class AsyncBytesIO(BytesIO):

    async def readline(self):
        return super().readline()


class Event(TestCase):
    """
    Parsing of Acme window events
    """

    def assertEvent(self, aBytes, origin, cause, start, end, flag, text):
        event = asyncio.run(WindowEvent.scan(AsyncBytesIO(aBytes)))
        self.assertEqual(event.origin, origin)
        self.assertEqual(event.cause, cause)
        self.assertEqual(event.start, start)
        self.assertEqual(event.end, end)
        self.assertEqual(event.flag, flag)
        self.assertEqual(event.text, text)

    def test_key_press(self):
        self.assertEvent(b'KI0 1 0 1 f\n', 'K', 'I', 0, 1, 0, 'f')

    def test_return_press(self):
        self.assertEvent(b'KI0 1 0 1 \n\n', 'K', 'I', 0, 1, 0, '\n')

    def test_multiline(self):
        self.assertEvent(b'ML0 13 0 13 cat\ndog\nmouse\n', 'M', 'L', 0, 13, 0, 'cat\ndog\nmouse')

    def test_look(self):
        self.assertEvent(b'ML1 1 2 0 \n', 'M', 'L', 1, 1, 2, '')

    def test_look_expanded(self):
        self.assertEvent(b'ML0 3 0 3 foo\n', 'M', 'L', 0, 3, 0, 'foo')

    def test_execute(self):
        self.assertEvent(b'Mx13 13 3 0 \n', 'M', 'x', 13, 13, 3, '')

    def test_execute_expanded(self):
        self.assertEvent(b'Mx12 15 0 3 Del\n', 'M', 'x', 12, 15, 0, 'Del')
