"""HandLang – keyboard-driven demo (Phase 3 deliverable).

Type token names separated by spaces to build and execute programs.
Example: ``REPEAT 4 FORWARD 100 TURN 90 END RUN`` draws a square.
"""

import logging
import sys

import config
from language.interpreter import Interpreter, InterpreterError, StepLimitExceeded
from language.parser import ParseError, Parser
from language.semantic import check
from language.tokens import NAME_TO_TOKEN, Token, TokenType
from runtime.canvas import TurtleCanvas


def setup_logging() -> None:
    """Configure the root logger from :mod:`config` constants."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
    )


def text_to_tokens(text: str) -> list[Token] | None:
    """Parse whitespace-separated text into pre-lexed tokens.

    Token names (``FORWARD``, ``REPEAT``, …) are mapped to their type.
    Bare integers are mapped directly to ``NUMBER`` tokens.

    Returns:
        Token list ending with EOF, or *None* on bad input.
    """
    tokens: list[Token] = []
    pos = 0

    for word in text.strip().split():
        upper = word.upper()

        if upper in NAME_TO_TOKEN:
            tokens.append(Token(NAME_TO_TOKEN[upper], position=pos))
        elif word.isdigit():
            tokens.append(Token(TokenType.NUMBER, value=int(word), position=pos))
        else:
            print(f"  Unknown token: '{word}' at position {pos}")
            return None
        pos += 1

    tokens.append(Token(TokenType.EOF, position=pos))
    return tokens


def run_program(text: str) -> None:
    """Tokenize, parse, check, execute, and render a HandLang program."""
    # 1. Tokenize
    tokens = text_to_tokens(text)
    if tokens is None:
        return

    names = [
        t.type.name + (f"({t.value})" if t.value is not None else "")
        for t in tokens
        if t.type != TokenType.EOF
    ]
    print(f"  Tokens: {names}")

    # 2. Parse
    try:
        parser = Parser(tokens)
        program = parser.parse()
    except ParseError as exc:
        print(f"  ✗ Parse error: {exc}")
        return

    print(f"  AST:    {program}")

    # 3. Semantic check
    errors = check(program)
    if errors:
        for err in errors:
            print(f"  ✗ Semantic error: {err}")
        return

    # 4. Interpret
    try:
        interp = Interpreter()
        commands = interp.execute(program)
    except StepLimitExceeded as exc:
        print(f"  ✗ Execution error: {exc}")
        return
    except InterpreterError as exc:
        print(f"  ✗ Runtime error: {exc}")
        return

    print(f"  ✓ Drawing {len(commands)} line segment(s)")

    # 5. Render
    if commands:
        canvas = TurtleCanvas()
        canvas.render(commands)
        print("  Canvas opened — close the window to continue.")
        canvas.show()
    else:
        print("  (nothing to draw)")


def main() -> None:
    """Interactive REPL for HandLang."""
    setup_logging()

    print("=" * 60)
    print("  HandLang – Keyboard Demo")
    print("=" * 60)
    print("  Type tokens separated by spaces.")
    print("  Example: REPEAT 4 FORWARD 100 TURN 90 END RUN")
    print()
    print("  Commands:  FORWARD  TURN  REPEAT … END  PEN_TOGGLE")
    print("             VAR  COLOR  RUN  + numbers")
    print("  Type 'quit' to exit.")
    print("=" * 60)

    while True:
        try:
            text = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not text:
            continue
        if text.lower() in ("quit", "exit"):
            break

        run_program(text)

    print("\nGoodbye!")


if __name__ == "__main__":
    main()
