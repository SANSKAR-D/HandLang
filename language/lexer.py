"""HandLang lexer.

Transforms a stream of raw gesture tokens into parser-ready tokens:
  - Combines consecutive DIGIT_x tokens into a single NUMBER token.
  - Handles UNDO by removing the most recently emitted token.
  - Preserves the original position (gesture index) for error reporting.
  - Appends EOF.
"""

import logging
from typing import Optional

from language.tokens import DIGIT_VALUES, Token, TokenType

logger = logging.getLogger(__name__)


def is_digit_token(token_type: TokenType) -> bool:
    """Return True if *token_type* is one of DIGIT_0 … DIGIT_9."""
    return token_type in DIGIT_VALUES


def lex(raw_tokens: list[Token]) -> list[Token]:
    """Lex a list of raw gesture tokens into parser-ready tokens.

    Args:
        raw_tokens: Tokens as emitted by the stabilizer or keyboard input,
                    potentially containing DIGIT_x and UNDO tokens.

    Returns:
        A list of tokens suitable for the parser, ending with EOF.
    """
    output: list[Token] = []
    i = 0

    while i < len(raw_tokens):
        token = raw_tokens[i]

        # ── UNDO: pop the last emitted token ──
        if token.type == TokenType.UNDO:
            if output:
                removed = output.pop()
                logger.info("UNDO: removed %s", removed)
            else:
                logger.warning("UNDO: nothing to undo")
            i += 1
            continue

        # ── Digit run: combine into a NUMBER ──
        if is_digit_token(token.type):
            digits: list[int] = []
            start_pos = token.position

            # Special case: after VAR or INC, only the FIRST digit is the variable ID.
            # Variable IDs are always single digits (v0–v9), so we must NOT
            # greedily merge them with the value digits that follow.
            prev_type = output[-1].type if output else None
            prev_is_var_or_inc = prev_type in (TokenType.VAR, TokenType.INC)
            if prev_is_var_or_inc:
                # Emit exactly one digit as the variable ID NUMBER
                digits.append(DIGIT_VALUES[raw_tokens[i].type])
                i += 1
            else:
                while i < len(raw_tokens) and is_digit_token(raw_tokens[i].type):
                    digits.append(DIGIT_VALUES[raw_tokens[i].type])
                    i += 1

            number = 0
            for d in digits:
                number = number * 10 + d

            output.append(Token(TokenType.NUMBER, value=number, position=start_pos))
            continue

        # ── Everything else: pass through ──
        output.append(Token(token.type, value=token.value, position=token.position))
        i += 1

    # Determine EOF position
    eof_pos = raw_tokens[-1].position + 1 if raw_tokens else 0
    output.append(Token(TokenType.EOF, position=eof_pos))
    return output
