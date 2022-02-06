from unittest import TestCase, skip
from unittest.mock import patch
from io import BytesIO
import asyncio

from cord import WindowEvent, PythonWindow, Editor


class AsyncBytesIO(BytesIO):
    async def readline(self):
        return super().readline()


class Tasks(TestCase):
    # TODO figure out how to test asyncio
    pass


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
        self.assertEvent(b"KI0 1 0 1 f\n", "K", "I", 0, 1, 0, "f")

    def test_return_press(self):
        self.assertEvent(b"KI0 1 0 1 \n\n", "K", "I", 0, 1, 0, "\n")

    def test_multiline(self):
        self.assertEvent(
            b"ML0 13 0 13 cat\ndog\nmouse\n", "M", "L", 0, 13, 0, "cat\ndog\nmouse"
        )

    def test_look(self):
        self.assertEvent(b"ML1 1 2 0 \n", "M", "L", 1, 1, 2, "")

    def test_look_expanded(self):
        self.assertEvent(b"ML0 3 0 3 foo\n", "M", "L", 0, 3, 0, "foo")

    def test_execute(self):
        self.assertEvent(b"Mx13 13 3 0 \n", "M", "x", 13, 13, 3, "")

    def test_execute_expanded(self):
        self.assertEvent(b"Mx12 15 0 3 Del\n", "M", "x", 12, 15, 0, "Del")


class WindowSetup(TestCase):
    """Creating a window executes the expected rope actions"""

    @skip
    def test_construct(self):
        with patch("rope.base.project.Project") as Project, patch.object(
            PythonWindow, "path"
        ) as path:
            window = PythonWindow(666)
            Project.find_module.assert_called_once_with(path)
            self.assertEqual(
                window.rope_module,
                Project.find_module.assert_called_once_with.return_value,
            )


class Look(TestCase):
    """Look events call rope symbol lookup"""

    @skip
    def test_handle_look(self):
        with patch(
            "rope.contrib.findit.find_definition"
        ) as find_definition, patch.object(
            PythonWindow, "rope_module"
        ) as module, patch.object(
            Editor, "rope_project"
        ) as project:
            window = Editor().window(666)
            text = Mock()
            start = Mock()
            event = WindowEvent("M", "L", start, None, None, text)
            window.handle_event(event)
            find_definition.assert_called_once_with(project, start, text)
