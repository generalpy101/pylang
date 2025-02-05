from errors import InterpreterRuntimeError
from tokens import Token


class Environment:
    def __init__(self, enclosing_scope: "Environment" = None) -> None:
        self.values = {}
        self.enclosing = enclosing_scope  # For scoping

    def define(self, name: str, value: object) -> None:
        self.values[name] = value

    def assign(self, name: Token, value: object) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        # If not in current scope, check enclosing scope
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise InterpreterRuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def get(self, name: Token) -> object:
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        # If not in current scope, check enclosing scope
        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise InterpreterRuntimeError(name, f"Undefined variable '{name.lexeme}'.")
