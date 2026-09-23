"""Turtle-graphics canvas using Tkinter.

Renders :class:`~language.interpreter.DrawCommand` objects produced by the
interpreter onto a Tkinter canvas widget.
"""

import tkinter as tk

import config
from language.interpreter import DrawCommand


class TurtleCanvas:
    """A Tkinter window that draws line segments from interpreter output."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("HandLang Canvas")
        self.canvas = tk.Canvas(
            self.root,
            width=config.CANVAS_WIDTH,
            height=config.CANVAS_HEIGHT,
            bg=config.CANVAS_BG_COLOR,
        )
        self.canvas.pack()

    def render(self, commands: list[DrawCommand]) -> None:
        """Clear the canvas and draw all *commands*.

        Coordinate system: the turtle's (0, 0) maps to the canvas center.
        Turtle-Y points up; screen-Y points down, so Y is flipped.
        """
        self.canvas.delete("all")
        cx = config.CANVAS_WIDTH / 2
        cy = config.CANVAS_HEIGHT / 2

        for cmd in commands:
            self.canvas.create_line(
                cx + cmd.x1,
                cy - cmd.y1,
                cx + cmd.x2,
                cy - cmd.y2,
                fill=cmd.color,
                width=2,
            )

    def show(self) -> None:
        """Enter the Tkinter event loop (blocks until window is closed)."""
        self.root.mainloop()

    def close(self) -> None:
        """Programmatically close the window."""
        self.root.destroy()
