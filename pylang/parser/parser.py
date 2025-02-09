from ast.expr import *
from ast.stmt import *
from typing import List

from lexer.token_type import TokenType
from lexer.tokens import Token
from utils.errors import ErrorType
from utils.logger import Logger


class ParserError(Exception):
    pass


class Parser:
    """
    Parser for the lox language
    Grammar used is:
    expression     → assignment ;
    assignment     → (call ".")? IDENTIFIER "=" assignment
                | logic_or ;
    logic_or       → logic_and ( "or" logic_and )* ;
    logic_and      → equality ( "and" equality )* ;
    equality       → comparison ( ( "!=" | "==" ) comparison )* ;
    comparison     → term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
    term           → factor ( ( "-" | "+" ) factor )* ;
    factor         → unary ( ( "/" | "*" ) unary )* ;
    unary          → ( "!" | "-" ) unary | call ;
    call           → primary ( "(" arguments? ")" | "." IDENTIFIER )* ;
    argumenst      → expression ( "," expression )* ;
    primary        → NUMBER | STRING | "true" | "false" | "nil"
                | "(" expression ")" | IDENTIFIER ;
    program        → declaration* EOF ;
    declaration    → classDecl
                | funDecl
                | varDecl
                | statement ;
    classDecl      → "class" IDENTIFIER "{" function* "}" ;
    funDecl        → "def" function ;
    function       → IDENTIFIER "(" parameters? ")" block ;
    parameters     → IDENTIFIER ( "," IDENTIFIER )* ;
    statement      → exprStmt
               | forStmt
               | ifStmt
               | printStmt
               | returnStmt
               | whileStmt
               | block ;
    returnStmt     → "return" expression? ";" ;
    forStmt        → "for" "(" ( varDecl | exprStmt | ";" )
                    expression? ";"
                    expression? ")" statement ;
    whileStmt      → "while" "(" expression ")" statement ;
    ifStmt         → "if" "(" expression ")" statement
                ( "else" statement )? ;
    block          → "{" declaration* "}" ;
    varDecl        → "var" IDENTIFIER ( "=" expression )? ";" ;
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
                evaluated_stmt = self._declaration()
                if evaluated_stmt is not None:
                    statements.append(evaluated_stmt)
            return statements
        except ParserError:
            return None
        except Exception as e:
            Logger.error(ErrorType.SyntaxError, self._peek().line, str(e))
            return None

    def _declaration(self) -> Stmt:
        try:
            if self._match(TokenType.CLASS):
                return self._class_declaration()
            if self._match(TokenType.DEF):
                return self._funtion_declaration("function")
            if self._match(TokenType.VAR):
                return self._var_declaration()
            return self._statement()
        except ParserError:
            self._synchronize()
            return None

    def _class_declaration(self) -> Stmt:
        name = self._consume(TokenType.IDENTIFIER, "Expected class name.")
        self._consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")

        methods = []

        while (
            not self._peek().token_type == TokenType.RIGHT_BRACE and not self._is_end()
        ):
            methods.append(self._funtion_declaration("method"))

        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")
        return ClassStmt(name=name, methods=methods)

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

        if self._match(TokenType.SELF):
            return Self(keyword=self._previous())

        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return expr

        if self._match(TokenType.IDENTIFIER):
            return Variable(self._previous())

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
