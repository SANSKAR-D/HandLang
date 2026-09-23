"""Phase 2 automated tests — T2.1 through T2.11."""

import pytest

from language import ast_nodes as ast
from language.lexer import lex
from language.parser import ParseError, Parser
from language.semantic import check
from language.tokens import Token, TokenType


# ── Lexer tests ─────────────────────────────────────────────────────────────


def test_T2_1_lexer_digit_combining() -> None:
    """T2.1: [DIGIT_1, DIGIT_0, DIGIT_0] → NUMBER(100)."""
    raw = [
        Token(TokenType.DIGIT_1, position=0),
        Token(TokenType.DIGIT_0, position=1),
        Token(TokenType.DIGIT_0, position=2),
    ]
    result = lex(raw)

    assert result[0].type == TokenType.NUMBER
    assert result[0].value == 100
    assert result[-1].type == TokenType.EOF


def test_T2_2_lexer_position_tracking() -> None:
    """T2.2: Each output token preserves the original gesture index."""
    raw = [
        Token(TokenType.FORWARD, position=0),
        Token(TokenType.DIGIT_5, position=1),
        Token(TokenType.DIGIT_0, position=2),
        Token(TokenType.TURN, position=3),
        Token(TokenType.DIGIT_9, position=4),
        Token(TokenType.DIGIT_0, position=5),
    ]
    result = lex(raw)

    # FORWARD(pos=0), NUMBER(50, pos=1), TURN(pos=3), NUMBER(90, pos=4), EOF
    assert result[0].type == TokenType.FORWARD and result[0].position == 0
    assert result[1].type == TokenType.NUMBER and result[1].value == 50 and result[1].position == 1
    assert result[2].type == TokenType.TURN and result[2].position == 3
    assert result[3].type == TokenType.NUMBER and result[3].value == 90 and result[3].position == 4


# ── Parser tests ────────────────────────────────────────────────────────────


def _tokens(*specs: tuple) -> list[Token]:
    """Helper to build a token list from (type, value?) tuples + EOF."""
    out = []
    for i, spec in enumerate(specs):
        if isinstance(spec, tuple):
            tt, val = spec
            out.append(Token(tt, value=val, position=i))
        else:
            out.append(Token(spec, position=i))
    out.append(Token(TokenType.EOF, position=len(specs)))
    return out


def test_T2_3_parser_square() -> None:
    """T2.3: REPEAT 4 FORWARD 100 TURN 90 END RUN → correct AST."""
    tokens = _tokens(
        TokenType.REPEAT, (TokenType.NUMBER, 4),
        TokenType.FORWARD, (TokenType.NUMBER, 100),
        TokenType.TURN, (TokenType.NUMBER, 90),
        TokenType.END, TokenType.RUN,
    )
    program = Parser(tokens).parse()

    expected = ast.Program([
        ast.Repeat(ast.NumberLiteral(4), [
            ast.Forward(ast.NumberLiteral(100)),
            ast.Turn(ast.NumberLiteral(90)),
        ]),
    ])
    assert program == expected


def test_T2_4_parser_pen_toggle() -> None:
    """T2.4: PEN_TOGGLE FORWARD 50 PEN_TOGGLE RUN → two PenToggles."""
    tokens = _tokens(
        TokenType.PEN_TOGGLE,
        TokenType.FORWARD, (TokenType.NUMBER, 50),
        TokenType.PEN_TOGGLE,
        TokenType.RUN,
    )
    program = Parser(tokens).parse()

    assert len(program.statements) == 3
    assert isinstance(program.statements[0], ast.PenToggle)
    assert isinstance(program.statements[1], ast.Forward)
    assert isinstance(program.statements[2], ast.PenToggle)


def test_T2_5_parser_nested_repeat() -> None:
    """T2.5: REPEAT 2 REPEAT 3 FORWARD 50 END END RUN → nested."""
    tokens = _tokens(
        TokenType.REPEAT, (TokenType.NUMBER, 2),
        TokenType.REPEAT, (TokenType.NUMBER, 3),
        TokenType.FORWARD, (TokenType.NUMBER, 50),
        TokenType.END, TokenType.END, TokenType.RUN,
    )
    program = Parser(tokens).parse()

    outer = program.statements[0]
    assert isinstance(outer, ast.Repeat)
    assert outer.count == ast.NumberLiteral(2)

    inner = outer.body[0]
    assert isinstance(inner, ast.Repeat)
    assert inner.count == ast.NumberLiteral(3)
    assert inner.body[0] == ast.Forward(ast.NumberLiteral(50))


def test_T2_6_parser_empty_program() -> None:
    """T2.6: RUN → Program([])."""
    tokens = _tokens(TokenType.RUN)
    program = Parser(tokens).parse()
    assert program == ast.Program([])


def test_T2_7_semantic_unmatched_repeat() -> None:
    """T2.7: REPEAT 4 FORWARD 100 RUN (no END) → ParseError."""
    tokens = _tokens(
        TokenType.REPEAT, (TokenType.NUMBER, 4),
        TokenType.FORWARD, (TokenType.NUMBER, 100),
        TokenType.RUN,
    )
    with pytest.raises(ParseError) as exc_info:
        Parser(tokens).parse()
    assert "END" in str(exc_info.value)


def test_T2_8_semantic_missing_operand() -> None:
    """T2.8: FORWARD END → ParseError about missing number."""
    tokens = _tokens(TokenType.FORWARD, TokenType.END, TokenType.RUN)
    with pytest.raises(ParseError) as exc_info:
        Parser(tokens).parse()
    assert "number" in str(exc_info.value).lower() or "NUMBER" in str(exc_info.value)


def test_T2_9_semantic_undefined_variable() -> None:
    """T2.9: FORWARD VAR 1 RUN (v1 not assigned) → semantic error."""
    tokens = _tokens(
        TokenType.FORWARD, TokenType.VAR, (TokenType.NUMBER, 1),
        TokenType.RUN,
    )
    program = Parser(tokens).parse()
    errors = check(program)

    assert len(errors) > 0
    assert "v1" in errors[0] or "undefined" in errors[0].lower()


def test_T2_10_parser_error_recovery() -> None:
    """T2.10: Invalid sequences don't crash; error has position info."""
    tokens = _tokens(TokenType.END, TokenType.RUN)
    with pytest.raises(ParseError) as exc_info:
        Parser(tokens).parse()
    # Error should mention the token position
    assert "Token" in str(exc_info.value)


def test_T2_11_color_statement() -> None:
    """T2.11: COLOR 3 FORWARD 100 RUN → Color(3) + Forward(100)."""
    tokens = _tokens(
        TokenType.COLOR, (TokenType.NUMBER, 3),
        TokenType.FORWARD, (TokenType.NUMBER, 100),
        TokenType.RUN,
    )
    program = Parser(tokens).parse()

    assert len(program.statements) == 2
    assert isinstance(program.statements[0], ast.Color)
    assert program.statements[0].color_id == ast.NumberLiteral(3)
