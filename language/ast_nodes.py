"""HandLang AST node definitions.

Each grammar production maps to a dataclass.  The tree is built by the
parser and walked by the interpreter.  All nodes use ``@dataclass`` so
equality comparison works automatically for testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


# ── Expressions (evaluate to a number) ──────────────────────────────────────


@dataclass
class NumberLiteral:
    """A literal integer, e.g. ``100``."""
    value: int


@dataclass
class VarRef:
    """A variable reference, e.g. ``v1``."""
    name: str


Expression = Union[NumberLiteral, VarRef]


# ── Statements ──────────────────────────────────────────────────────────────


@dataclass
class Forward:
    """Move the turtle forward by *distance* units."""
    distance: Expression


@dataclass
class Turn:
    """Turn the turtle left by *angle* degrees."""
    angle: Expression


@dataclass
class PenToggle:
    """Toggle the pen (up ↔ down)."""
    pass


@dataclass
class Color:
    """Set the pen color by index into ``config.TURTLE_COLORS``."""
    color_id: Expression


@dataclass
class Repeat:
    """Execute *body* statements *count* times."""
    count: Expression
    body: list  # list[Statement]


@dataclass
class Assign:
    """Assign *value* to variable ``v{var_id}``."""
    var_id: int
    value: Expression


Statement = Union[Forward, Turn, PenToggle, Color, Repeat, Assign]


# ── Program (root node) ────────────────────────────────────────────────────


@dataclass
class Program:
    """Root AST node containing a list of statements."""
    statements: list  # list[Statement]
