from typing import Dict, List

from ast_pylang.expr import *
from ast_pylang.stmt import *
from interpreter.callable import Callable
from interpreter.environment import Environment
from interpreter.pylang_class import PylangClass
from interpreter.pylang_function import PylangFunction
from interpreter.pylang_instance import PylangInstance
from lexer.token_type import TokenType
from lexer.tokens import Token
from stdlib.builtins import ClockCallable
from utils.errors import (Break, Continue, ErrorType, InterpreterRuntimeError,
                          Return)
from utils.logger import Logger


class Interpreter(ExprVisitor, StmtVisitor):
    def __init__(self) -> None:
        self.globals = Environment()
        self.environment: Environment = self.globals
        self.locals: Dict[Token, int] = {}

        self.globals.define("clock", ClockCallable())

    def interpret(self, stmts: List[Stmt]) -> None:
        _execute = self._execute
        try:
            for statement in stmts:
                _execute(statement)
        except InterpreterRuntimeError as e:
            Logger.error(ErrorType.RuntimeError, e.token.line, e.message)
            # Raise the error to the caller to exit the program
            raise e
        except Break as e:
            Logger.error(
                ErrorType.RuntimeError, e.token.line, "Break statement outside of loop."
            )
            # Return the error to the caller to exit the program
            raise InterpreterRuntimeError(e.token, "Break statement outside of loop.")
        except Continue as e:
            Logger.error(
                ErrorType.RuntimeError,
                e.token.line,
                "Continue statement outside of loop.",
            )
            # Return the error to the caller to exit the program
            raise InterpreterRuntimeError(
                e.token, "Continue statement outside of loop."
            )
        except RecursionError as e:
            Logger.error(
                ErrorType.RuntimeError,
                0,
                "Stack overflow.",
            )
            # Raise as InterpreterRuntimeError to handle the error
            # Set token as first token in the file
            raise InterpreterRuntimeError(
                Token(TokenType.EOF, "", None, 0), "Stack overflow."
            )

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

    def visit_class_stmt(self, stmt: ClassStmt):
        superclass = None
        if stmt.superclass is not None:
            superclass = self._evaluate(stmt.superclass)
            if not isinstance(superclass, PylangClass):
                raise InterpreterRuntimeError(
                    stmt.superclass.name, "Superclass must be a class."
                )

        self.environment.define(stmt.name.lexeme, None)

        if stmt.superclass is not None:
            self.environment = Environment(enclosing_scope=self.environment)
            self.environment.define("super", superclass)

        methods = {}
        for method in stmt.methods:
            function = PylangFunction(
                declaration=method,
                closure=self.environment,
                is_initializer=(method.name.lexeme == "init"),
            )
            methods[method.name.lexeme] = function

        kclass = PylangClass(
            name=stmt.name.lexeme, superclass=superclass, methods=methods
        )

        if superclass is not None:
            self.environment = self.environment.enclosing

        self.environment.assign(stmt.name, kclass)

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

    def visit_self(self, expr: Self):
        return self._look_up_variable(expr.keyword, expr)

    def visit_function_expr(self, expr: FunctionExpr):
        return PylangFunction(
            declaration=expr, closure=self.environment, is_initializer=False
        )

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
            try:
                self._execute(expr.body)
            except Break:
                break
            except Continue:
                continue

        return None

    def visit_break_stmt(self, stmt: BreakStmt):
        # Raise a custom exception to handle the break statement
        # This will allow us to jump through the call stack and return the value
        raise Break(token=stmt.keyword)

    def visit_continue_stmt(self, stmt: ContinueStmt):
        # Raise a custom exception to handle the continue statement
        # This will allow us to jump through the call stack and return the value
        raise Continue(token=stmt.keyword)

    def visit_variable(self, expr: Variable):
        return self._look_up_variable(expr.name, expr)

    def visit_get(self, expr: Get):
        obj: PylangInstance = self._evaluate(expr.object)
        if isinstance(obj, PylangInstance):
            return obj.get(expr.name)

        raise InterpreterRuntimeError(expr.name, "Only instances have properties.")

    def visit_set(self, expr: SetExpr):
        obj: PylangInstance | None = self._evaluate(expr.object)

        if not isinstance(obj, PylangInstance):
            raise InterpreterRuntimeError(expr.name, "Only instances have fields.")

        value = self._evaluate(expr.value)
        obj.set(expr.name, value)
        return value

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
            if right == 0:
                raise InterpreterRuntimeError(
                    expr.operator, "Division by zero is not allowed."
                )
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
        function = PylangFunction(
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

    def visit_super(self, expr: Super):
        distance = self.locals[expr]
        superclass: Super = self.environment.get_at(distance, "super")

        obj = self.environment.get_at(distance - 1, "this")
        method = superclass.find_method(expr.method.lexeme)

        if method is None:
            raise InterpreterRuntimeError(
                expr.method, f"Undefined property '{expr.method.lexeme}'."
            )

        return method.bind(obj)

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
