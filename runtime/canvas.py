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
            bg="#050505",  # Hacker Dark background
            highlightthickness=0
        )
        self.canvas.pack()
        
        self.commands_to_draw = []
        self.draw_index = 0
        self.cx = config.CANVAS_WIDTH / 2
        self.cy = config.CANVAS_HEIGHT / 2

    def render(self, commands: list[DrawCommand]) -> None:
        """Clear the canvas and start drawing all *commands* animated."""
        self.canvas.delete("all")
        self.commands_to_draw = commands
        self.draw_index = 0
        self._animate_draw()

    def _animate_draw(self) -> None:
        """Draw the next segment and schedule the next frame."""
        if self.draw_index >= len(self.commands_to_draw):
            return

        # High-speed animation: draw multiple segments per frame if there are many
        batch_size = 3
        
        for _ in range(batch_size):
            if self.draw_index >= len(self.commands_to_draw):
                break
                
            cmd = self.commands_to_draw[self.draw_index]
            # Use Hacker Green if no specific color is provided, else the provided color
            color = "#00FF41" if cmd.color == "black" else cmd.color
            
            self.canvas.create_line(
                self.cx + cmd.x1,
                self.cy - cmd.y1,
                self.cx + cmd.x2,
                self.cy - cmd.y2,
                fill=color,
                width=2,
            )
            self.draw_index += 1
            
        # Schedule next frame in 10ms (high speed)
        self.root.after(10, self._animate_draw)

    def show(self) -> None:
        """Enter the Tkinter event loop (blocks until window is closed)."""
        self.root.mainloop()

    def close(self) -> None:
        """Programmatically close the window."""
        self.root.destroy()
