import sys

from logger import Logger
from scanner import Scanner

def run(source_code: str):
    lexical_scanner = Scanner(source_code=source_code)
    tokens = lexical_scanner.scan_tokens()
    
    print(tokens)

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
        Logger.error("Test", 69, e)


if __name__ == "__main__":
    argument_length = len(sys.argv)
    if argument_length > 2:
        print("Usage: python lox.py [script]")
    elif argument_length == 2:
        run_file(file_path=sys.argv[1])
    else:
        run_repl()
