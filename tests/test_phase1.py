"""Phase 1 automated tests — T1.1 through T1.5."""

import os

from language.ast_nodes import Forward, NumberLiteral, Program, Repeat, Turn
from language.tokens import Token, TokenType


def test_T1_1_all_token_types_defined() -> None:
    """T1.1: All 10+ gesture tokens and DIGIT tokens exist."""
    for name in (
        "FORWARD", "TURN", "REPEAT", "END", "PEN_TOGGLE",
        "VAR", "COLOR", "IF", "RUN", "UNDO",
    ):
        assert hasattr(TokenType, name), f"TokenType.{name} missing"

    for i in range(10):
        assert hasattr(TokenType, f"DIGIT_{i}"), f"TokenType.DIGIT_{i} missing"

    assert hasattr(TokenType, "NUMBER")
    assert hasattr(TokenType, "EOF")


def test_T1_2_token_dataclass() -> None:
    """T1.2: Token fields accessible, equality works."""
    t1 = Token(TokenType.FORWARD, position=3)
    assert t1.type == TokenType.FORWARD
    assert t1.position == 3
    assert t1.value is None

    t2 = Token(TokenType.NUMBER, value=42, position=5)
    assert t2.value == 42

    t3 = Token(TokenType.FORWARD, position=3)
    assert t1 == t3


def test_T1_3_ast_node_construction() -> None:
    """T1.3: Build Program(Forward(100), Turn(90)) and access fields."""
    prog = Program([
        Forward(NumberLiteral(100)),
        Turn(NumberLiteral(90)),
    ])
    assert len(prog.statements) == 2
    assert isinstance(prog.statements[0], Forward)
    assert prog.statements[0].distance.value == 100  # type: ignore[union-attr]
    assert isinstance(prog.statements[1], Turn)


def test_T1_4_ast_node_equality() -> None:
    """T1.4: Two identical ASTs compare equal; different ones do not."""
    prog1 = Program([
        Repeat(NumberLiteral(4), [
            Forward(NumberLiteral(100)),
            Turn(NumberLiteral(90)),
        ]),
    ])
    prog2 = Program([
        Repeat(NumberLiteral(4), [
            Forward(NumberLiteral(100)),
            Turn(NumberLiteral(90)),
        ]),
    ])
    assert prog1 == prog2

    prog3 = Program([Forward(NumberLiteral(50))])
    assert prog1 != prog3


def test_T1_5_grammar_file_exists() -> None:
    """T1.5: grammar.md exists and contains EBNF rules."""
    path = os.path.join("language", "grammar.md")
    assert os.path.isfile(path), f"{path} not found"

    text = open(path, encoding="utf-8").read()
    for keyword in ("program", "statement", "forward", "turn", "repeat", "number"):
        assert keyword in text, f"Grammar missing rule for '{keyword}'"
