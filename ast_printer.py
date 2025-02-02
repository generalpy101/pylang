from expr import Binary, Expr, ExprVisitor, Grouping, Literal, Unary
from token_type import TokenType
from tokens import Token


class AstPrinter(ExprVisitor):
    def print(self, expr: Expr):
        return expr.accept(self)

    def visit_binary(self, expr: Binary):
        left = expr.left.accept(self)
        right = expr.right.accept(self)

        return f"{left} {expr.operator.lexeme} {right}"

    def visit_grouping(self, expr: Grouping):
        return f"(group {expr.expression.accept(self)})"

    def visit_literal(self, expr: Literal):
        return str(expr.value)

    def visit_unary(self, expr: Unary):
        right = expr.right.accept(self)
        return f"({expr.operator.lexeme}{right})"


if __name__ == "__main__":
    # 11 - (-10)
    bin_exp = Binary(
        left=Grouping(expression=Literal(value=11)),
        operator=Token(token_type=TokenType.MINUS, lexeme="-", literal=None, line=0),
        right=Unary(
            operator=Token(
                token_type=TokenType.MINUS, lexeme="-", literal=None, line=0
            ),
            right=Literal(10),
        ),
    )
    printer = AstPrinter()
    print(printer.print(expr=bin_exp))
