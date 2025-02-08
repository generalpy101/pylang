import time
from ast.expr import (Assign, Binary, Expr, ExprVisitor, Grouping, Literal,
                      Logical, Unary, Variable)
from ast.stmt import (BlockStmt, ExpressionStmt, IfStmt, PrintStmt, ReturnStmt,
                      Stmt, StmtVisitor, VarStmt, WhileStmt)
from typing import Dict, List

from interpreter.callable import Callable
from interpreter.environment import Environment
from interpreter.lox_function import LoxFunction
from lexer.token_type import TokenType
from lexer.tokens import Token
from stdlib.builtins import ClockCallable
from utils.errors import ErrorType, InterpreterRuntimeError, Return
from utils.logger import Logger


class Interpreter(ExprVisitor, StmtVisitor):
    def __init__(self) -> None:
        self.globals = Environment()
        self.environment = self.globals
        self.locals: Dict[Token, int] = {}

        self.globals.define("clock", ClockCallable())

    def interpret(self, stmts: List[Stmt]) -> None:
        try:
            for statement in stmts:
                self._execute(statement)
        except InterpreterRuntimeError as e:
            Logger.error(ErrorType.RuntimeError, e.token.line, e.message)
            # Raise the error to the caller to exit the program
            raise e

    def resolve(self, expr: Expr, depth: int):
        self.locals[expr] = depth

    def execute_block(self, stmts: List[Stmt], environment: Environment) -> None:
        # This method is just a public wrapper around _execute_block
        self._execute_block(stmts, environment)

    def visit_block_stmt(self, expr: BlockStmt):
        self._execute_block(
            expr.statements, Environment(enclosing_scope=self.environment)
        )
        return None

    def visit_var_stmt(self, expr: VarStmt):
        value = None
        if expr.initializer is not None:
            value = self._evaluate(expr.initializer)

        self.environment.define(expr.name.lexeme, value)
        return None

    def visit_assign(self, expr: Assign):
        value = self._evaluate(expr.value)
        distance = self.locals.get(expr)

        if distance is not None:
            self.environment.assign_at(distance, expr.name, value)
        else:
            self.globals.assign(expr.name, value)
        return value

    def visit_expression_stmt(self, stmt: ExpressionStmt) -> None:
        self._evaluate(stmt.expression)

    def visit_if_stmt(self, expr: IfStmt):
        if self._is_truthy(self._evaluate(expr.condition)):
            self._execute(expr.then_branch)
        elif expr.else_branch is not None:
            self._execute(expr.else_branch)

        return None

    def visit_print_stmt(self, stmt: PrintStmt) -> None:
        value = self._evaluate(stmt.expression)
        print(self._stringify(value))

    def visit_literal(self, expr: Literal) -> object:
        return expr.value

    def visit_grouping(self, expr: Grouping) -> object:
        return self._evaluate(expr.expression)

    def visit_unary(self, expr: Unary) -> object | None:
        right = self._evaluate(expr.right)

        if expr.operator.token_type == TokenType.MINUS:
            self._check_number_operand(expr.operator, right)
            return -float(right)
        elif expr.operator.token_type == TokenType.BANG:
            return not self._is_truthy(right)

        return None

    def visit_logical(self, expr: Logical):
        left = self._evaluate(expr.left)

        if expr.operator.token_type == TokenType.OR:
            if self._is_truthy(left):
                return left
        else:
            if not self._is_truthy(left):
                return left

        return self._evaluate(expr.right)

    def visit_while_stmt(self, expr: WhileStmt):
        while self._is_truthy(self._evaluate(expr.condition)):
            self._execute(expr.body)

        return None

    def visit_variable(self, expr: Variable):
        return self._look_up_variable(expr.name, expr)

    def visit_binary(self, expr: Binary) -> object | None:
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)

        # Arithmetic
        if expr.operator.token_type == TokenType.PLUS:
            # If both operands are strings, concatenate them
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            # If one of the operands is a string, convert the other to a string. Similar to JavaScript
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            # If both operands are numbers, add them
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return float(left) + float(right)

            self._check_number_operands(expr.operator, left, right)
        elif expr.operator.token_type == TokenType.MINUS:
            self._check_number_operands(expr.operator, left, right)
            return float(left) - float(right)
        elif expr.operator.token_type == TokenType.STAR:
            self._check_number_operands(expr.operator, left, right)
            return float(left) * float(right)
        elif expr.operator.token_type == TokenType.SLASH:
            self._check_number_operands(expr.operator, left, right)
            return float(left) / float(right)
        # Comparison
        # These operators are only defined for numbers for now
        elif expr.operator.token_type == TokenType.GREATER:
            self._check_number_operands(expr.operator, left, right)
            return float(left) > float(right)
        elif expr.operator.token_type == TokenType.GREATER_EQUAL:
            self._check_number_operands(expr.operator, left, right)
            return float(left) >= float(right)
        elif expr.operator.token_type == TokenType.LESS:
            self._check_number_operands(expr.operator, left, right)
            return float(left) < float(right)
        elif expr.operator.token_type == TokenType.LESS_EQUAL:
            self._check_number_operands(expr.operator, left, right)
            return float(left) <= float(right)
        # Equality
        elif expr.operator.token_type == TokenType.BANG_EQUAL:
            return not self._is_equal(left, right)
        elif expr.operator.token_type == TokenType.EQUAL_EQUAL:
            return self._is_equal(left, right)
        return None

    def visit_call(self, expr):
        callee = self._evaluate(expr.callee)
        arguments = [self._evaluate(arg) for arg in expr.arguments]

        if not isinstance(callee, Callable):
            raise InterpreterRuntimeError(
                expr.paren, "Can only call functions and classes."
            )

        if len(arguments) != callee.arity():
            raise InterpreterRuntimeError(
                expr.paren,
                f"Expected {callee.arity()} arguments but got {len(arguments)}.",
            )

        return callee.call(self, arguments)

    def visit_function_stmt(self, expr):
        function = LoxFunction(
            declaration=expr, closure=self.environment, is_initializer=False
        )
        self.environment.define(expr.name.lexeme, function)
        return None

    def visit_return_stmt(self, stmt: ReturnStmt):
        value = None
        if stmt.value != None:
            value = self._evaluate(stmt.value)

        # Raise a custom exception to handle the return statement
        # This will allow us to jump through the call stack and return the value
        raise Return(value)

    def _is_truthy(self, obj: object) -> bool:
        if obj is None:
            return False

        if isinstance(obj, bool):
            return bool(obj)

        return True

    def _is_equal(self, a: object, b: object) -> bool:
        if a is None and b is None:
            return True

        if a == None:
            return False

        return a == b

    def _evaluate(self, expr: Expr) -> object:
        return expr.accept(self)

    def _stringify(self, obj: object) -> str:
        if obj is None:
            return "nil"

        if isinstance(obj, float):
            text = str(obj)
            if text.endswith(".0"):
                text = text[:-2]
            return text

        return str(obj)

    def _check_number_operand(self, operator: Token, operand: object) -> None:
        if isinstance(operand, (int, float)):
            return

        raise InterpreterRuntimeError(
            token=operator,
            message=f"Operands must be numbers for operator {operator.lexeme}",
        )

    def _check_number_operands(
        self, operator: Token, left: object, right: object
    ) -> None:
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return

        raise InterpreterRuntimeError(
            token=operator,
            message=f"Operands must be numbers for operator {operator.lexeme}",
        )

    def _execute(self, stmt: Stmt) -> None:
        stmt.accept(self)

    def _execute_block(self, stmts: List[Stmt], environment: Environment) -> None:
        previous = self.environment
        try:
            self.environment = environment
            for statement in stmts:
                self._execute(statement)
        finally:
            self.environment = previous

    def _look_up_variable(self, name: Token, expr: Expr):
        distance = self.locals.get(expr)

        if distance is not None:
            return self.environment.get_at(distance, name.lexeme)
        else:
            return self.globals.get(name)
