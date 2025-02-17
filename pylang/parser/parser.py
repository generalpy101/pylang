from typing import List

from ast_pylang.expr import *
from ast_pylang.stmt import *
from lexer.token_type import TokenType
from lexer.tokens import Token
from utils.errors import ErrorType
from utils.logger import Logger


class ParserError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.current = 0
        self.had_error = False

    def parse(self) -> Expr | None:
        try:
            statements = []
            while not self._is_end():
                evaluated_stmt = self._declaration()
                if evaluated_stmt is not None:
                    statements.append(evaluated_stmt)
            return statements if not self.had_error else None
        except ParserError:
            return None
        except Exception as e:
            Logger.error(ErrorType.SyntaxError, self._peek().line, str(e))
            return None

    def _error(self, token: Token, message: str):
        Logger.error(ErrorType.SyntaxError, token.line, message)
        self.had_error = True
        raise ParserError(message)

    def _declaration(self) -> Stmt:
        try:
            if self._match(TokenType.CLASS):
                return self._class_declaration()
            if self._match(TokenType.DEF):
                # If next token is IDENTIFIER then it is a function declaration
                if self._peek().token_type == TokenType.IDENTIFIER:
                    return self._funtion_declaration("function")
                # Else it is a function expression which means it is an anonymous function
                return ExpressionStmt(expression=self._function_expr())
            if self._match(TokenType.VAR):
                return self._var_declaration()
            return self._statement()
        except ParserError:
            self._synchronize()
            return None

    def _class_declaration(self) -> Stmt:
        name = self._consume(TokenType.IDENTIFIER, "Expected class name.")
        superclass: Variable | None = None

        if self._match(TokenType.COLON):
            self._consume(TokenType.IDENTIFIER, "Expect superclass name.")
            superclass = Variable(self._previous())

        self._consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")

        methods = []

        while (
            not self._peek().token_type == TokenType.RIGHT_BRACE and not self._is_end()
        ):
            methods.append(self._funtion_declaration("method"))

        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")
        return ClassStmt(name=name, superclass=superclass, methods=methods)

    def _funtion_declaration(self, kind: str) -> Stmt:
        name = self._consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self._consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        parameters = []

        # Consume parameters
        if not self._peek().token_type == TokenType.RIGHT_PAREN:
            parameters.append(
                self._consume(TokenType.IDENTIFIER, "Expect parameter name.")
            )
            while self._match(TokenType.COMMA):
                if len(parameters) >= 255:
                    Logger.error(
                        ErrorType.SyntaxError,
                        self._peek().line,
                        "Cannot have more than 255 parameters.",
                    )
                parameters.append(
                    self._consume(TokenType.IDENTIFIER, "Expect parameter name.")
                )

        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        # Consume body
        self._consume(TokenType.LEFT_BRACE, f"Expect '{'{'}' before {kind} body.")
        body = self._block()
        return FunctionStmt(name=name, params=parameters, body=body)

    def _function_expr(self) -> Expr:
        # Since it is an anonymous function, it does not have a name
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'def'.")
        parameters = []

        if not self._peek().token_type == TokenType.RIGHT_PAREN:
            parameters.append(
                self._consume(TokenType.IDENTIFIER, "Expect parameter name.")
            )
            while self._match(TokenType.COMMA):
                if len(parameters) >= 255:
                    Logger.error(
                        ErrorType.SyntaxError,
                        self._peek().line,
                        "Cannot have more than 255 parameters.",
                    )
                parameters.append(
                    self._consume(TokenType.IDENTIFIER, "Expect parameter name.")
                )

        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")
        self._consume(TokenType.LEFT_BRACE, "Expect '{' before function body.")

        body = self._block()

        return FunctionExpr(
            params=parameters, body=body
        )  # Anonymous function expression

    def _var_declaration(self) -> Stmt:
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name.")

        initializer = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()

        self._consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return VarStmt(name=name, initializer=initializer)

    def _statement(self) -> Stmt:
        if self._match(TokenType.FOR):
            return self._for_statement()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.BREAK) or self._match(TokenType.CONTINUE):
            return self._break_continue_statement()
        if self._match(TokenType.LEFT_BRACE):
            return BlockStmt(statements=self._block())
        return self._expression_statement()

    def _block(self) -> List[Stmt]:
        statements = []

        while (
            not self._peek().token_type == TokenType.RIGHT_BRACE and not self._is_end()
        ):
            statements.append(self._declaration())

        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def _print_statement(self) -> Stmt:
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return PrintStmt(expression=value)

    def _return_statement(self) -> Stmt:
        keyword = self._previous()
        value = None
        if not (self._peek().token_type == TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after return value.")

        return ReturnStmt(keyword=keyword, value=value)

    def _for_statement(self) -> Stmt:
        """
        This is C style for loop but in backend it is just a syntactic sugar
        for the while loop. We will desugar it to while loop.
        """
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        # Handle initialiser part
        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.VAR):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()

        # Handle condition part
        condition = None
        if self._peek().token_type != TokenType.SEMICOLON:
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        # Handle increment part
        increment = None
        if not self._peek().token_type == TokenType.RIGHT_PAREN:
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self._statement()
        if increment is not None:
            body = BlockStmt(statements=[body, ExpressionStmt(expression=increment)])
        if condition is None:
            condition = Literal(True)
        body = WhileStmt(condition=condition, body=body)
        if initializer is not None:
            body = BlockStmt(statements=[initializer, body])
        return body

    def _if_statement(self) -> Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch = self._statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()

        return IfStmt(
            condition=condition, then_branch=then_branch, else_branch=else_branch
        )

    def _while_statement(self) -> Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after while condition.")

        body = self._statement()
        return WhileStmt(condition=condition, body=body)

    def _break_continue_statement(self) -> Stmt:
        keyword = self._previous()
        stmt = None

        if keyword.token_type == TokenType.BREAK:
            stmt = BreakStmt(keyword=keyword)
        elif keyword.token_type == TokenType.CONTINUE:
            stmt = ContinueStmt(keyword=keyword)

        self._consume(TokenType.SEMICOLON, "Expect ';' after break/continue statement.")

        return stmt

    def _expression_statement(self) -> Stmt:
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return ExpressionStmt(expression=value)

    def _expression(self) -> Expr:
        return self._assignment()

    def _assignment(self) -> Expr:
        expr = self._or()

        if self._match(TokenType.EQUAL):
            equals = self._previous()
            value = self._assignment()

            if isinstance(expr, Variable):
                name = expr.name
                return Assign(name=name, value=value)
            elif isinstance(expr, Get):
                return SetExpr(object=expr.object, name=expr.name, value=value)

            Logger.error(
                ErrorType.SyntaxError, equals.line, "Invalid assignment target."
            )

        return expr

    def _or(self) -> Expr:
        expr = self._and()

        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._and()
            expr = Logical(left=expr, operator=operator, right=right)

        return expr

    def _and(self) -> Expr:
        expr = self._equality()

        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expr = Logical(left=expr, operator=operator, right=right)

        return expr

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

        return self._call()

    def _call(self) -> Expr:
        expr = self._primary()

        while True:
            if self._match(TokenType.LEFT_PAREN):
                expr = self._finish_call(expr)
            elif self._match(TokenType.DOT):
                name = self._consume(
                    TokenType.IDENTIFIER, "Expect property name after '.'."
                )
                expr = Get(object=expr, name=name)
            else:
                break

        return expr

    def _finish_call(self, callee: Expr) -> Expr:
        arguments = []
        if not self._peek().token_type == TokenType.RIGHT_PAREN:
            arguments.append(self._expression())
            while self._match(TokenType.COMMA):
                if len(arguments) >= 255:
                    Logger.error(
                        ErrorType.SyntaxError,
                        self._peek().line,
                        "Cannot have more than 255 arguments.",
                    )
                arguments.append(self._expression())
        paren = self._consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
        return Call(callee=callee, paren=paren, arguments=arguments)

    def _primary(self) -> Expr:
        if self._match(TokenType.FALSE):
            return Literal(False)
        if self._match(TokenType.TRUE):
            return Literal(True)
        if self._match(TokenType.NIL):
            return Literal(None)

        if self._match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self._previous().literal)

        if self._match(TokenType.SUPER):
            keyword = self._previous()
            self._consume(TokenType.DOT, "Expected '.' after 'super'.")
            method = self._consume(
                TokenType.IDENTIFIER, "Expected superclass method name."
            )
            return Super(keyword=keyword, method=method)

        if self._match(TokenType.SELF):
            return Self(keyword=self._previous())

        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return expr

        if self._match(TokenType.DEF):
            # If next token is def it is an anonymous function
            return self._function_expr()

        if self._match(TokenType.IDENTIFIER):
            return Variable(self._previous())

        self._error(self._peek(), "Expected expression.")

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._match(token_type):
            return self._previous()

        current_token = self._peek()
        if current_token.token_type == TokenType.EOF:
            self._error(current_token, message)
        else:
            self._error(current_token, message)

    def _synchronize(self):
        self._advance()

        while not self._is_end():
            if self._previous().token_type == TokenType.SEMICOLON:
                return

            if self._peek().token_type in [
                TokenType.CLASS,
                TokenType.DEF,
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
