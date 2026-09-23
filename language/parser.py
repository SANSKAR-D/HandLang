"""HandLang recursive-descent parser.

One function per grammar rule.  Builds an AST from a list of lexed tokens.
Raises :class:`ParseError` with gesture-aware position info on failure.
"""

import logging

from language import ast_nodes as ast
from language.tokens import Token, TokenType

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Raised when the parser encounters an unexpected token."""

    def __init__(self, message: str, token: Token | None = None):
        self.token = token
        if token is not None:
            full = f"Token {token.position}: {message} (got {token.type.name})"
        else:
            full = message
        super().__init__(full)


class Parser:
    """Recursive-descent parser for the HandLang grammar.

    Usage::

        parser = Parser(tokens)
        program = parser.parse()   # returns ast.Program or raises ParseError
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── Helpers ─────────────────────────────────────────────────────────────

    def current(self) -> Token:
        """Return the token at the current position without consuming it."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, position=self.pos)

    def advance(self) -> Token:
        """Consume and return the current token."""
        token = self.current()
        self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        """Consume and return the current token if it matches *token_type*.

        Raises:
            ParseError: if the current token does not match.
        """
        token = self.current()
        if token.type != token_type:
            raise ParseError(
                f"Expected {token_type.name}, got {token.type.name}",
                token,
            )
        return self.advance()

    # ── Grammar rules ───────────────────────────────────────────────────────

    def parse(self) -> ast.Program:
        """``program ::= statement* RUN``"""
        statements = self._parse_statements()
        self.expect(TokenType.RUN)
        return ast.Program(statements)

    def _parse_statements(self) -> list:
        """Parse zero or more statements until END, RUN, or EOF."""
        stmts: list = []
        stop = {TokenType.END, TokenType.RUN, TokenType.EOF}
        while self.current().type not in stop:
            stmts.append(self._parse_statement())
        return stmts

    def _parse_statement(self):
        """Dispatch to the correct statement parser."""
        tt = self.current().type

        if tt == TokenType.FORWARD:
            return self._parse_forward()
        if tt == TokenType.TURN:
            return self._parse_turn()
        if tt == TokenType.PEN_TOGGLE:
            return self._parse_pen_toggle()
        if tt == TokenType.COLOR:
            return self._parse_color()
        if tt == TokenType.REPEAT:
            return self._parse_repeat()
        if tt == TokenType.VAR:
            return self._parse_assign()

        raise ParseError(
            f"Unexpected token {tt.name}; expected a statement",
            self.current(),
        )

    def _parse_forward(self) -> ast.Forward:
        """``forward ::= FORWARD number``"""
        self.expect(TokenType.FORWARD)
        return ast.Forward(self._parse_number())

    def _parse_turn(self) -> ast.Turn:
        """``turn ::= TURN number``"""
        self.expect(TokenType.TURN)
        return ast.Turn(self._parse_number())

    def _parse_pen_toggle(self) -> ast.PenToggle:
        """``pen ::= PEN_TOGGLE``"""
        self.expect(TokenType.PEN_TOGGLE)
        return ast.PenToggle()

    def _parse_color(self) -> ast.Color:
        """``color ::= COLOR number``"""
        self.expect(TokenType.COLOR)
        return ast.Color(self._parse_number())

    def _parse_repeat(self) -> ast.Repeat:
        """``repeat ::= REPEAT number statement* END``"""
        self.expect(TokenType.REPEAT)
        count = self._parse_number()
        body = self._parse_statements()
        self.expect(TokenType.END)
        return ast.Repeat(count, body)

    def _parse_assign(self) -> ast.Assign:
        """``assign ::= VAR NUMBER number``"""
        self.expect(TokenType.VAR)
        var_id_token = self.expect(TokenType.NUMBER)
        value = self._parse_number()
        return ast.Assign(var_id_token.value, value)

    def _parse_number(self):
        """``number ::= NUMBER | VAR NUMBER``

        Returns a :class:`NumberLiteral` or :class:`VarRef`.
        """
        token = self.current()

        if token.type == TokenType.NUMBER:
            self.advance()
            return ast.NumberLiteral(token.value)

        if token.type == TokenType.VAR:
            self.advance()
            var_id_token = self.expect(TokenType.NUMBER)
            return ast.VarRef(f"v{var_id_token.value}")

        raise ParseError(
            f"Expected a number, got {token.type.name}",
            token,
        )
