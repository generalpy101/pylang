from ast_pylang.expr import *
from ast_pylang.stmt import *
from enum import Enum
from typing import Dict, List

from interpreter.interpreter import Interpreter
from lexer.tokens import Token
from utils.errors import ResolverError
from utils.logger import Logger


class FunctionType(Enum):
    NONE = "NONE"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    INITIALIZER = "INITIALIZER"


class ClassType(Enum):
    NONE = "NONE"
    CLASS = "CLASS"
    SUBCLASS = "SUBCLASS"


class Resolver(ExprVisitor, StmtVisitor):
    def __init__(self, interpreter: Interpreter) -> None:
        self.interpreter = interpreter
        self.scopes: List[Dict[str, bool]] = []
        self.current_function = FunctionType.NONE
        self.current_class = ClassType.NONE

    def resolve_statements(self, statements: List[Stmt]):
        for statement in statements:
            try:
                self._resolve_stmt(statement)
            except ResolverError as e:
                Logger.error(
                    error_type=e.error_type, line=e.token.line, message=e.message
                )
                raise e

    def visit_block_stmt(self, stmt: BlockStmt):
        self._begin_scope()
        self.resolve_statements(statements=stmt.statements)
        self._end_scope()

    def visit_var_stmt(self, stmt: VarStmt):
        self._declare(stmt.name.lexeme)
        if stmt.initializer is not None:
            self._resolve_expr(stmt.initializer)
        self._define(stmt.name.lexeme)

    def visit_variable(self, expr: Variable):
        if len(self.scopes) > 0:
            exists_in_current_scope = self.scopes[-1].get(expr.name.lexeme)
            if exists_in_current_scope is False:
                raise ResolverError(
                    token=expr.name,
                    message=f"Cannot read local variable in its own initializer",
                )

        self._resolve_local(expr, expr.name.lexeme)

    def visit_assign(self, expr: Assign):
        self._resolve_expr(expr.value)
        self._resolve_local(expr, expr.name.lexeme)

    def visit_function_stmt(self, stmt: FunctionStmt):
        self._declare(stmt.name.lexeme)
        self._define(stmt.name.lexeme)

        self._resolve_function(stmt, FunctionType.FUNCTION)

    def visit_expression_stmt(self, expression_stmt: ExpressionStmt):
        self._resolve_expr(expression_stmt.expression)

    def visit_if_stmt(self, stmt: IfStmt):
        self._resolve_expr(stmt.condition)
        self._resolve_stmt(stmt.then_branch)
        if stmt.else_branch is not None:
            self._resolve_stmt(stmt.else_branch)

    def visit_print_stmt(self, stmt: PrintStmt):
        self._resolve_expr(stmt.expression)

    def visit_return_stmt(self, stmt: ReturnStmt):
        if self.current_function == FunctionType.NONE:
            raise ResolverError(stmt.keyword, "Cannot return from top-level code")

        if stmt.value is not None:
            if self.current_function == FunctionType.INITIALIZER:
                raise ResolverError(
                    stmt.keyword, "Cannot return a value from an initializer"
                )
            self._resolve_expr(stmt.value)

    def visit_while_stmt(self, stmt: WhileStmt):
        self._resolve_expr(stmt.condition)
        self._resolve_stmt(stmt.body)

    def visit_class_stmt(self, stmt: ClassStmt):
        enclosing_class = self.current_class
        self.current_class = ClassType.CLASS
        self._declare(stmt.name.lexeme)
        self._define(stmt.name.lexeme)

        if (
            stmt.superclass is not None
            and stmt.name.lexeme == stmt.superclass.name.lexeme
        ):
            raise ResolverError(
                stmt.superclass.name, "A class cannot inherit from itself"
            )

        if stmt.superclass is not None:
            self.current_class = ClassType.SUBCLASS
            self._resolve_expr(stmt.superclass)

        if stmt.superclass is not None:
            self._begin_scope()
            self.scopes[-1]["super"] = True

        self._begin_scope()
        self.scopes[-1]["self"] = True

        for method in stmt.methods:
            declaration = FunctionType.METHOD
            if method.name.lexeme == "init":
                declaration = FunctionType.INITIALIZER
            self._resolve_function(method, declaration)

        self._end_scope()

        if stmt.superclass is not None:
            self._end_scope()

        self.current_class = enclosing_class

    def visit_binary(self, expr: Binary):
        self._resolve_expr(expr.left)
        self._resolve_expr(expr.right)

    def visit_call(self, expr: Call):
        self._resolve_expr(expr.callee)

        for argument in expr.arguments:
            self._resolve_expr(argument)

    def visit_grouping(self, expr: Grouping):
        self._resolve_expr(expr.expression)

    def visit_literal(self, expr: Literal):
        return None

    def visit_logical(self, expr: Logical):
        self._resolve_expr(expr.left)
        self._resolve_expr(expr.right)

    def visit_unary(self, expr: Unary):
        self._resolve_expr(expr.right)

    def visit_get(self, expr: Get):
        self._resolve_expr(expr.object)

    def visit_set(self, expr: SetExpr):
        self._resolve_expr(expr.value)
        self._resolve_expr(expr.object)

    def visit_self(self, expr: Self):
        if self.current_class == ClassType.NONE:
            raise ResolverError(expr.keyword, "Cannot use 'self' outside of a class")

        self._resolve_local(expr, expr.keyword.lexeme)

    def visit_super(self, expr: Super):
        if self.current_class == ClassType.NONE:
            raise ResolverError(expr.keyword, "Cannot use 'super' outside of a class")
        elif self.current_class != ClassType.SUBCLASS:
            raise ResolverError(
                expr.keyword, "Cannot use 'super' in a class with no superclass"
            )
        self._resolve_local(expr, expr.keyword.lexeme)

    def _declare(self, name: str):
        if len(self.scopes) == 0:
            return
        scope = self.scopes[-1]
        if name in scope:
            raise Exception(f"Variable with name {name} already declared in this scope")
        scope[name] = False

    def _define(self, name: str):
        if len(self.scopes) == 0:
            return
        scope = self.scopes[-1]
        scope[name] = True

    def _begin_scope(self):
        self.scopes.append({})

    def _end_scope(self):
        self.scopes.pop()

    def _resolve_local(self, expr: Expr, name: str):
        for i in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[i]:
                self.interpreter.resolve(expr, len(self.scopes) - 1 - i)
                return

    def _resolve_function(self, function: FunctionStmt, type: FunctionType):
        enclosing_function: FunctionType = self.current_function
        self.current_function = type
        self._begin_scope()
        for param in function.params:
            self._declare(param.lexeme)
            self._define(param.lexeme)

        self.resolve_statements(function.body)
        self._end_scope()
        self.current_function = enclosing_function

    def _resolve_stmt(self, statement: Stmt):
        statement.accept(self)

    def _resolve_expr(self, expression: Expr):
        expression.accept(self)
