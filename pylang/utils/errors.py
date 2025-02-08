from enum import Enum

from lexer.tokens import Token


class ErrorType(Enum):
    LexicalError = "LexicalError"
    SyntaxError = "SyntaxError"
    RuntimeError = "RuntimeError"
    ResolverError = "ResolverError"


class InterpreterRuntimeError(Exception):
    def __init__(self, token: Token, message: str) -> None:
        self.token = token
        self.message = message
        super().__init__(message)


class ResolverError(Exception):
    def __init__(self, token: Token, message: str) -> None:
        self.token = token
        self.message = message
        self.error_type = ErrorType.ResolverError
        super().__init__(message)


class Return(Exception):
    def __init__(self, value: object) -> None:
        self.value = value
        super().__init__(value)
