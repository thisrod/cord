from unittest import TestCase, skip
from unittest.mock import patch, Mock, PropertyMock
from io import BytesIO
import asyncio

import cord
from cord import WindowEvent, PythonWindow, Editor
from rope.base.exceptions import BadIdentifierError


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


class Window(TestCase):
    def test_window_path(self):
        """window.path makes the appropriate Acme queries"""
        with patch(
            "cord.nine_file_content", return_value="/tmp/foo.py Del Snarf"
        ) as mock_nfc:
            window = PythonWindow(Mock(), 123)
            path = window.path
            mock_nfc.assert_called_with("acme/123/tag")
            self.assertEqual(path, "/tmp/foo.py")

    def test_window_content(self):
        """window.content makes the appropriate Acme queries"""
        with patch(
            "cord.nine_file_content") as mock_nfc:
            window = PythonWindow(Mock(), 123)
            text = window.content
            mock_nfc.assert_called_with("acme/123/body")
            self.assertEqual(text, mock_nfc.return_value)

class RopeCalls(TestCase):
    # Acme character addresses and Python strings both count from 0
    # Acme and Rope both count lines from 1

    def test_construct_project(self):
        """Constructing Editor constructs a Rope project for the current directory"""
        with patch("cord.Project") as Project:
            project_path = Mock()
            editor = Editor(event_tasks=None, project_path=project_path)
            Project.assert_called_once_with(project_path)
            self.assertEqual(editor.rope_project, Project.return_value)

    def test_construct_module(self):
        """Creating a window executes the expected rope actions"""
        with patch.object(PythonWindow, "path") as path:
            project = Mock()
            window = PythonWindow(project, 666)
            project.find_module.assert_called_once_with(path)
            self.assertEqual(
                window.rope_module,
                project.find_module.return_value,
            )

    def test_look_finds_definition(self):
        """Look events call rope symbol lookup"""
        with patch("cord.find_definition") as find_definition, patch(
            "cord.plumb"
        ) as plumb, patch.object(
            PythonWindow, "content", PropertyMock()
        ) as fake_content:
            project = Mock()
            window = PythonWindow(project, 666)
            text = fake_content.return_value
            start = 1234
            event = WindowEvent("M", "L", start, None, None, "")
            window.handle_event(event)
            expanded_event = WindowEvent("M", "L", start, None, None, Mock())
            window.handle_event(expanded_event)
            find_definition.assert_called_once_with(project, text, start)

    def test_look_plumbs_import(self):
        """Look events call plumb with another file"""
        with patch("cord.find_definition") as find_definition, patch(
            "cord.plumb"
        ) as plumb, patch.object(
            PythonWindow, "content", PropertyMock()
        ):
            project = Mock()
            window = PythonWindow(project, 666)
            event = WindowEvent("M", "L", 1234, None, None, Mock())
            window.handle_event(event)
            path = find_definition.return_value.resource.path
            lineno = find_definition.return_value.lineno
            plumb.assert_called_once_with(path, lineno)

    def test_look_plumbs_internal(self):
        """Look events call plumb with this file"""
        with patch("cord.find_definition") as find_definition, patch.object(PythonWindow, "path"), patch(
            "cord.plumb"
        ) as plumb, patch.object(
            PythonWindow, "content", PropertyMock()
        ):
            project = Mock()
            window = PythonWindow(project, 666)
            find_definition.return_value.resource = None
            event = WindowEvent("M", "L", 1234, None, None, Mock())
            window.handle_event(event)
            plumb.assert_called_once_with(
                window.path, find_definition.return_value.lineno
            )

    def test_look_not_definition(self):
        """A look event that doesn't find a Python definition is handled normally"""
        with patch("cord.find_definition") as find_definition, patch.object(PythonWindow, "path"), patch(
            "cord.plumb"
        ) as plumb, patch.object(
            PythonWindow, "content", PropertyMock()
        ), patch("cord.nine_write_file") as mock_send:
            project = Mock()
            window = PythonWindow(project, 666)
            find_definition.side_effect = BadIdentifierError
            event = WindowEvent("M", "L", 1234, 1244, None, Mock())
            window.handle_event(event)
            mock_send.assert_called_once_with("acme/666/event", "ML1234 1244\n")
            plumb.assert_not_called()

    def test_execute_title_bar(self):
        """An execute event in the title bar is handled normally"""
        with patch("cord.nine_write_file") as mock_send:
            project = Mock()
            window = PythonWindow(project, 666)
            event = WindowEvent("M", "x", 1234, 1244, None, Mock())
            window.handle_event(event)
            mock_send.assert_called_once_with("acme/666/event", "Mx1234 1244\n")
