"""HandLang semantic checker.

Walks an AST produced by the parser and reports semantic errors:
  - Undefined variables used before assignment.
  - (Future: type errors, unreachable code, etc.)

The checker is deliberately separate from the parser so that syntactically
valid but semantically wrong programs get a clear, distinct error.
"""

from language import ast_nodes as ast


class SemanticError(Exception):
    """Raised when the semantic checker finds an error."""


def check(program: ast.Program) -> list[str]:
    """Check *program* for semantic errors.

    Returns:
        A list of human-readable error strings (empty means all clear).
    """
    errors: list[str] = []
    defined_vars: set[str] = set()

    def check_statements(stmts: list) -> None:
        for stmt in stmts:
            check_statement(stmt)

    def check_statement(stmt: object) -> None:
        if isinstance(stmt, ast.Forward):
            check_expr(stmt.distance)
        elif isinstance(stmt, ast.Turn):
            check_expr(stmt.angle)
        elif isinstance(stmt, ast.Color):
            check_expr(stmt.color_id)
        elif isinstance(stmt, ast.Repeat):
            check_expr(stmt.count)
            check_statements(stmt.body)
        elif isinstance(stmt, ast.Assign):
            check_expr(stmt.value)
            defined_vars.add(f"v{stmt.var_id}")
        elif isinstance(stmt, ast.PenToggle):
            pass
        else:
            errors.append(f"Unknown statement type: {type(stmt).__name__}")

    def check_expr(expr: object) -> None:
        if isinstance(expr, ast.VarRef):
            if expr.name not in defined_vars:
                errors.append(f"Undefined variable '{expr.name}'")
        elif isinstance(expr, ast.NumberLiteral):
            pass
        else:
            errors.append(f"Unknown expression type: {type(expr).__name__}")

    check_statements(program.statements)
    return errors
