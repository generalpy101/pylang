from enum import Enum

from tokens import Token


class ErrorType(Enum):
    LexicalError = "LexicalError"
    SyntaxError = "SyntaxError"
    RuntimeError = "RuntimeError"


class InterpreterRuntimeError(Exception):
    def __init__(self, token: Token, message: str) -> None:
        self.token = token
        self.message = message
        super().__init__(message)
