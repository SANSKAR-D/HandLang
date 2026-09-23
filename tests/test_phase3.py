"""Phase 3 automated tests — T3.1 through T3.7."""

import pytest

import config
from language import ast_nodes as ast
from language.interpreter import Interpreter, StepLimitExceeded


def test_T3_1_interpreter_forward() -> None:
    """T3.1: Forward(100) moves turtle 100 in the current heading (east)."""
    interp = Interpreter()
    prog = ast.Program([ast.Forward(ast.NumberLiteral(100))])
    commands = interp.execute(prog)

    assert len(commands) == 1
    # Default heading = 0 (east) → x increases, y stays 0
    assert abs(interp.turtle.x - 100.0) < 0.01
    assert abs(interp.turtle.y - 0.0) < 0.01


def test_T3_2_interpreter_turn() -> None:
    """T3.2: Turn(90) changes heading by 90 degrees."""
    interp = Interpreter()
    prog = ast.Program([ast.Turn(ast.NumberLiteral(90))])
    interp.execute(prog)

    assert abs(interp.turtle.heading - 90.0) < 0.01


def test_T3_3_interpreter_repeat_square() -> None:
    """T3.3: Repeat(4, [Forward(100), Turn(90)]) returns turtle to origin."""
    interp = Interpreter()
    prog = ast.Program([
        ast.Repeat(ast.NumberLiteral(4), [
            ast.Forward(ast.NumberLiteral(100)),
            ast.Turn(ast.NumberLiteral(90)),
        ]),
    ])
    commands = interp.execute(prog)

    assert len(commands) == 4
    assert abs(interp.turtle.x) < 0.01
    assert abs(interp.turtle.y) < 0.01


def test_T3_4_interpreter_pen_toggle() -> None:
    """T3.4: PenToggle makes the second Forward not draw."""
    interp = Interpreter()
    prog = ast.Program([
        ast.Forward(ast.NumberLiteral(50)),   # pen down → draws
        ast.PenToggle(),                      # pen up
        ast.Forward(ast.NumberLiteral(50)),   # pen up → no draw
    ])
    commands = interp.execute(prog)

    assert len(commands) == 1  # only the first segment


def test_T3_5_interpreter_variables() -> None:
    """T3.5: Assign(1, 50) then Forward(VarRef('v1')) → moves 50."""
    interp = Interpreter()
    prog = ast.Program([
        ast.Assign(1, ast.NumberLiteral(50)),
        ast.Forward(ast.VarRef("v1")),
    ])
    commands = interp.execute(prog)

    assert len(commands) == 1
    assert abs(interp.turtle.x - 50.0) < 0.01


def test_T3_6_interpreter_step_limit() -> None:
    """T3.6: Huge repeat → StepLimitExceeded, no hang."""
    interp = Interpreter()
    prog = ast.Program([
        ast.Repeat(ast.NumberLiteral(999_999), [
            ast.Forward(ast.NumberLiteral(1)),
        ]),
    ])

    with pytest.raises(StepLimitExceeded):
        interp.execute(prog)


def test_T3_7_interpreter_color() -> None:
    """T3.7: Color(2) changes draw color to the third entry."""
    interp = Interpreter()
    prog = ast.Program([
        ast.Color(ast.NumberLiteral(2)),
        ast.Forward(ast.NumberLiteral(100)),
    ])
    commands = interp.execute(prog)

    assert len(commands) == 1
    assert commands[0].color == config.TURTLE_COLORS[2]
