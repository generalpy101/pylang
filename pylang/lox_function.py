from typing import List

from callable import Callable
from environment import Environment
from errors import Return
from stmt import FunctionStmt


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
            return r.value

        return None

    def arity(self):
        return len(self.declaration.params)

    def __str__(self):
        return f"<fn>{self.declaration.name.lexeme}"
