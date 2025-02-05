import sys
from parser import Parser
from typing import List

from errors import ErrorType
from interpreter import Interpreter, InterpreterRuntimeError
from scanner import Scanner
from stmt import Stmt
from tokens import Token


def run(source_code: str, is_repl: bool = False):
    try:
        lexical_scanner: Scanner = Scanner(source_code=source_code)
        tokens: List[Token] = lexical_scanner.scan_tokens()
        parser: Parser = Parser(tokens=tokens)
        expressions: List[Stmt] | None = parser.parse()

        if expressions is None:
            if not is_repl:
                exit(64)
            return

        interpreter: Interpreter = Interpreter()
        interpreter.interpret(stmts=expressions)
    except InterpreterRuntimeError as e:
        if not is_repl:
            exit(70)


def run_file(file_path: str):
    with open(file_path, "r") as file:
        run(source_code=file.read())


def run_repl():
    try:
        while True:
            command = input(">> ")
            run(source_code=command, is_repl=True)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    argument_length = len(sys.argv)
    if argument_length > 2:
        print("Usage: python lox.py [script]")
    elif argument_length == 2:
        run_file(file_path=sys.argv[1])
    else:
        run_repl()
