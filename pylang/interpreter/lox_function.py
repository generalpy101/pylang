from ast_pylang.stmt import FunctionStmt
from typing import List

from interpreter.callable import Callable
from interpreter.environment import Environment
from utils.errors import Return


class LoxFunction(Callable):
    def __init__(
        self, declaration: FunctionStmt, closure: Environment, is_initializer: bool
    ):
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer

    def call(self, interpreter: "Interpreter", arguments: List[object]):
        environment = Environment(enclosing_scope=self.closure)

        for i, param in enumerate(self.declaration.params):
            environment.define(param.lexeme, arguments[i])

        try:
            interpreter.execute_block(self.declaration.body, environment)
        except Return as r:
            if self.is_initializer:
                return self.closure.get_at(0, "self")
            return r.value

        if self.is_initializer:
            return self.closure.get_at(0, "self")

        return None

    def arity(self):
        return len(self.declaration.params)

    def bind(self, instance: "LoxInstance"):
        environment = Environment(enclosing_scope=self.closure)
        environment.define("self", instance)
        return LoxFunction(self.declaration, environment, self.is_initializer)

    def __str__(self):
        return f"<fn>{self.declaration.name.lexeme}"
