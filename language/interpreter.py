"""HandLang visitor-based interpreter.

Walks the AST produced by the parser, maintaining turtle state and
emitting :class:`DrawCommand` objects that the canvas can render.
"""

import logging
import math
from dataclasses import dataclass

import config
from language import ast_nodes as ast

logger = logging.getLogger(__name__)


# ── Output types ────────────────────────────────────────────────────────────


@dataclass
class DrawCommand:
    """A line segment to be rendered on the canvas."""

    x1: float
    y1: float
    x2: float
    y2: float
    color: str


@dataclass
class TurtleState:
    """Current state of the virtual turtle."""

    x: float = 0.0
    y: float = 0.0
    heading: float = 0.0      # degrees; 0 = east/right
    pen_down: bool = True
    color_index: int = 0


# ── Exceptions ──────────────────────────────────────────────────────────────


class StepLimitExceeded(Exception):
    """Raised when the interpreter exceeds ``config.MAX_INTERPRETER_STEPS``."""


class InterpreterError(Exception):
    """Raised on runtime errors (undefined var, bad expression, etc.)."""


# ── Interpreter ─────────────────────────────────────────────────────────────


class Interpreter:
    """Walk an AST and produce draw commands.

    Usage::

        interp = Interpreter()
        commands = interp.execute(program)
    """

    def __init__(self) -> None:
        self.turtle = TurtleState()
        self.draw_commands: list[DrawCommand] = []
        self.variables: dict[str, int] = {}
        self.steps: int = 0

    # ── Public API ──────────────────────────────────────────────────────

    def execute(self, program: ast.Program) -> list[DrawCommand]:
        """Execute *program* and return the resulting draw commands."""
        self.turtle = TurtleState()
        self.draw_commands = []
        self.variables = {}
        self.steps = 0

        for stmt in program.statements:
            self._visit(stmt)

        return self.draw_commands

    # ── Internals ───────────────────────────────────────────────────────

    def _check_step_limit(self) -> None:
        self.steps += 1
        if self.steps > config.MAX_INTERPRETER_STEPS:
            raise StepLimitExceeded(
                f"Program exceeded maximum step limit of "
                f"{config.MAX_INTERPRETER_STEPS}"
            )

    def _visit(self, node: object) -> None:
        """Dispatch to the correct visitor method."""
        self._check_step_limit()

        if isinstance(node, ast.Forward):
            self._visit_forward(node)
        elif isinstance(node, ast.Turn):
            self._visit_turn(node)
        elif isinstance(node, ast.PenToggle):
            self._visit_pen_toggle()
        elif isinstance(node, ast.Color):
            self._visit_color(node)
        elif isinstance(node, ast.Repeat):
            self._visit_repeat(node)
        elif isinstance(node, ast.Assign):
            self._visit_assign(node)
        elif isinstance(node, ast.Inc):
            self._visit_inc(node)
        else:
            raise InterpreterError(f"Unknown node type: {type(node).__name__}")

    def _eval_expr(self, expr: object) -> int:
        """Evaluate an expression node to an integer."""
        if isinstance(expr, ast.NumberLiteral):
            return expr.value
        if isinstance(expr, ast.VarRef):
            if expr.name not in self.variables:
                raise InterpreterError(f"Undefined variable: {expr.name}")
            return self.variables[expr.name]
        raise InterpreterError(f"Unknown expression type: {type(expr).__name__}")

    # ── Visitor methods ─────────────────────────────────────────────────

    def _visit_forward(self, node: ast.Forward) -> None:
        distance = self._eval_expr(node.distance)
        rad = math.radians(self.turtle.heading)
        new_x = self.turtle.x + distance * math.cos(rad)
        new_y = self.turtle.y + distance * math.sin(rad)

        if self.turtle.pen_down:
            color = config.TURTLE_COLORS[
                self.turtle.color_index % len(config.TURTLE_COLORS)
            ]
            self.draw_commands.append(
                DrawCommand(self.turtle.x, self.turtle.y, new_x, new_y, color)
            )

        self.turtle.x = new_x
        self.turtle.y = new_y

    def _visit_turn(self, node: ast.Turn) -> None:
        angle = self._eval_expr(node.angle)
        self.turtle.heading = (self.turtle.heading + angle) % 360

    def _visit_pen_toggle(self) -> None:
        self.turtle.pen_down = not self.turtle.pen_down

    def _visit_color(self, node: ast.Color) -> None:
        self.turtle.color_index = self._eval_expr(node.color_id)

    def _visit_repeat(self, node: ast.Repeat) -> None:
        count = self._eval_expr(node.count)
        for _ in range(count):
            for stmt in node.body:
                self._visit(stmt)

    def _visit_assign(self, node: ast.Assign) -> None:
        value = self._eval_expr(node.value)
        var_name = f"v{node.var_id}"
        self.variables[var_name] = value
        logger.info("Variable %s = %d", var_name, value)

    def _visit_inc(self, node: ast.Inc) -> None:
        amount = self._eval_expr(node.amount)
        var_name = f"v{node.var_id}"
        if var_name not in self.variables:
            raise InterpreterError(
                f"INC: variable '{var_name}' used before assignment"
            )
        self.variables[var_name] += amount
        logger.info("Variable %s += %d → %d", var_name, amount, self.variables[var_name])
