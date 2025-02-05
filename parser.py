from typing import List

from errors import ErrorType
from expr import Binary, Expr, Literal, Unary
from stmt import ExpressionStmt, PrintStmt, Stmt
from token_type import TokenType
from tokens import Token
from utils.logger import Logger


class ParserError(Exception):
    pass


class Parser:
    """
    Parser for the lox language
    Grammar used is:
    expression     → equality ;
    equality       → comparison ( ( "!=" | "==" ) comparison )* ;
    comparison     → term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
    term           → factor ( ( "-" | "+" ) factor )* ;
    factor         → unary ( ( "/" | "*" ) unary )* ;
    unary          → ( "!" | "-" ) unary
                | primary ;
    primary        → NUMBER | STRING | "true" | "false" | "nil"
                | "(" expression ")" ;

    program        → statement* EOF ;

    statement      → exprStmt
                | printStmt ;

    exprStmt       → expression ";" ;
    printStmt      → "print" expression ";" ;
    """

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Expr | None:
        try:
            statements = []
            while not self._is_end():
                statements.append(self._statement())
            return statements
        except ParserError:
            return None
        except Exception as e:
            Logger.error(ErrorType.SyntaxError, self._peek().line, str(e))
            return None

    def _statement(self) -> Stmt:
        if self._match(TokenType.PRINT):
            return self._print_statement()
        return self._expression_statement()

    def _print_statement(self) -> Stmt:
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return PrintStmt(expression=value)

    def _expression_statement(self) -> Stmt:
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return ExpressionStmt(expression=value)

    def _expression(self) -> Expr:
        return self._equality()

    def _equality(self) -> Expr:
        expr = self._comparison()

        while self._match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expr = Binary(left=expr, operator=operator, right=right)

        return expr

    def _comparison(self) -> Expr:
        expr = self._term()

        while self._match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator = self._previous()
            right = self._term()
            expr = Binary(left=expr, operator=operator, right=right)

        return expr

    def _term(self) -> Expr:
        expr = self._factor()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._factor()
            expr = Binary(left=expr, operator=operator, right=right)

        return expr

    def _factor(self) -> Expr:
        expr = self._unary()

        while self._match(TokenType.SLASH, TokenType.STAR):
            operator = self._previous()
            right = self._unary()
            expr = Binary(left=expr, operator=operator, right=right)

        return expr

    def _unary(self) -> Expr:
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            right = self._unary()
            return Unary(operator=operator, right=right)

        return self._primary()

    def _primary(self) -> Expr:
        if self._match(TokenType.FALSE):
            return Literal(False)
        if self._match(TokenType.TRUE):
            return Literal(True)
        if self._match(TokenType.NIL):
            return Literal(None)

        if self._match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self._previous().literal)

        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return expr

        Logger.error(ErrorType.SyntaxError, self._peek().line, "Expected expression.")

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._match(token_type):
            return self._previous()

        current_token = self._peek()
        if current_token.token_type == TokenType.EOF:
            Logger.error(
                ErrorType.SyntaxError,
                current_token.line,
                "Unexpected end of the code." + message,
            )
            raise ParserError("Unexpected end of the code." + message)
        else:
            Logger.error(ErrorType.SyntaxError, current_token.line, message)
            raise ParserError(message)

    def _synchronize(self):
        self._advance()

        while not self._is_end():
            if self._previous().token_type == TokenType.SEMICOLON:
                return

            if self._peek().token_type in [
                TokenType.CLASS,
                TokenType.FUN,
                TokenType.VAR,
                TokenType.FOR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.PRINT,
                TokenType.RETURN,
            ]:
                return

            self._advance()

    def _match(self, *types: TokenType) -> bool:
        if self._is_end():
            return False

        if self._peek().token_type in types:
            self._advance()
            return True

        return False

    def _is_end(self) -> bool:
        return self._peek().token_type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _advance(self) -> Token:
        if not self._is_end():
            self.current += 1

        return self._previous()

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]
