import sys
from parser import Parser
from typing import List

from ast_printer import AstPrinter
from expr import Expr
from scanner import Scanner
from tokens import Token
from utils.logger import Logger


def run(source_code: str):
    lexical_scanner: Scanner = Scanner(source_code=source_code)
    tokens: List[Token] = lexical_scanner.scan_tokens()
    parser: Parser = Parser(tokens=tokens)
    expression: Expr | None = parser.parse()

    if expression is None:
        return

    print(AstPrinter().print(expression))


def run_file(file_path: str):
    with open(file_path, "r") as file:
        run(source_code=file.read())


def run_repl():
    try:
        while True:
            command = input(">> ")
            run(source_code=command)
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
