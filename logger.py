from errors import ErrorType

class Logger:
    @classmethod
    def error(cls, error_type: ErrorType, line: int | str, message: str):
        print(f"{error_type.value} on {line}: {message}")
