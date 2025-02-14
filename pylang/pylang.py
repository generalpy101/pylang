import sys
from ast_pylang.stmt import Stmt
from parser.parser import Parser
from typing import List

from interpreter.interpreter import Interpreter, InterpreterRuntimeError
from interpreter.resolver import Resolver, ResolverError
from lexer.scanner import Scanner
from lexer.tokens import Token


def run(source_code: str, is_repl: bool = False):
    try:
        lexical_scanner: Scanner = Scanner(source_code=source_code)
        tokens: List[Token] = lexical_scanner.scan_tokens()
        parser: Parser = Parser(tokens=tokens)
        statements: List[Stmt] | None = parser.parse()

        if statements is None:
            if not is_repl:
                exit(64)
            return

        interpreter: Interpreter = Interpreter()
        resolver: Resolver = Resolver(interpreter=interpreter)
        resolver.resolve_statements(statements)
        interpreter.interpret(stmts=statements)

    except (InterpreterRuntimeError, ResolverError):
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
