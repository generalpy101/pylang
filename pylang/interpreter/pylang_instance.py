from lexer.tokens import Token
from utils.errors import InterpreterRuntimeError


class PylangInstance:
    __slots__ = ("klass", "fields")

    def __init__(self, klass: "PylangClass"):
        self.klass = klass
        self.fields = {}

    def get(self, name: Token):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        method = self.klass.find_method(name.lexeme)
        if method is not None:
            return method.bind(self)

        raise InterpreterRuntimeError(name, f"Undefined property '{name.lexeme}'")

    def set(self, name: Token, value):
        self.fields[name.lexeme] = value

    def __str__(self):
        return f"{self.klass.name} instance"
