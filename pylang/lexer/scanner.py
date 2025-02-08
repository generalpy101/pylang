import string
from typing import List

from utils.errors import ErrorType
from lexer.token_type import TokenType
from lexer.tokens import Token
from utils.logger import Logger

WHITESPACES_TO_IGNORE = [" ", "\t", "\r"]
STRING_IDENTIFIERS = ['"']
VALID_IDENTIFIER_CHARACTERS = string.ascii_lowercase + string.ascii_uppercase + "_"
KEYWORDS = {
    "and": TokenType.AND,
    "class": TokenType.CLASS,
    "else": TokenType.ELSE,
    "false": TokenType.FALSE,
    "for": TokenType.FOR,
    "def": TokenType.DEF,
    "if": TokenType.IF,
    "nil": TokenType.NIL,
    "or": TokenType.OR,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
    "super": TokenType.SUPER,
    "this": TokenType.THIS,
    "true": TokenType.TRUE,
    "var": TokenType.VAR,
    "while": TokenType.WHILE,
}


class Scanner:
    def __init__(self, source_code: str) -> None:
        self.source_code = source_code
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> List[Token]:
        while not self._is_end():
            self.start = self.current
            self._scan_token()

        self.tokens.append(
            Token(token_type=TokenType.EOF, lexeme="", literal=None, line=self.line)
        )
        return self.tokens

    def _scan_token(self):
        element = self._advance()
        if element == "(":
            self._add_token(TokenType.LEFT_PAREN)
        elif element == ")":
            self._add_token(TokenType.RIGHT_PAREN)
        elif element == "{":
            self._add_token(TokenType.LEFT_BRACE)
        elif element == "}":
            self._add_token(TokenType.RIGHT_BRACE)
        elif element == ",":
            self._add_token(TokenType.COMMA)
        elif element == ".":
            self._add_token(TokenType.DOT)
        elif element == "-":
            self._add_token(TokenType.MINUS)
        elif element == "+":
            self._add_token(TokenType.PLUS)
        elif element == ";":
            self._add_token(TokenType.SEMICOLON)
        elif element == "*":
            self._add_token(TokenType.STAR)
        elif element == "!":
            self._add_token(
                TokenType.BANG_EQUAL if self._match("=") else TokenType.BANG
            )
        elif element == "=":
            self._add_token(
                TokenType.EQUAL_EQUAL if self._match("=") else TokenType.EQUAL
            )
        elif element == "<":
            self._add_token(
                TokenType.LESS_EQUAL if self._match("=") else TokenType.LESS
            )
        elif element == ">":
            self._add_token(
                TokenType.GREATER_EQUAL if self._match("=") else TokenType.GREATER
            )
        elif element == "/":
            # // means it is a comment so ignore all characters till new line
            if self._match("/"):
                while self._peek() != "\n" and not self._is_end():
                    self._advance()
            else:
                self._add_token(TokenType.SLASH)
        elif element in WHITESPACES_TO_IGNORE:
            pass
        elif element == "\n":
            self.line += 1
        elif element in STRING_IDENTIFIERS:
            self._handle_strings()
        elif element.isdigit():
            self._handle_numbers()
        else:
            if self._is_alpha(element):
                # Parse identifiers. We'll use maximal munching rule here
                # When two lexical grammar rules can both match a chunk of code that the scanner is looking at, whichever one matches the most characters wins.
                self._handle_identifiers()
                return
            Logger.error(
                error_type=ErrorType.LexicalError,
                line=self.line,
                message=f"Unexpected character {element}",
            )

    def _is_end(self) -> bool:
        return self.current >= len(self.source_code)

    def _advance(self) -> str:
        char = self.source_code[self.current]
        self.current += 1
        return char

    def _add_token(self, token_type: TokenType, literal=None) -> None:
        code = self.source_code[self.start : self.current]
        self.tokens.append(
            Token(token_type=token_type, lexeme=code, literal=literal, line=self.line)
        )

    def _match(self, expected: str) -> bool:
        if self._is_end():
            return False

        if self.source_code[self.current] != expected:
            return False

        self.current += 1
        return True

    def _peek(self) -> str:
        if self.current >= len(self.source_code):
            return "\0"
        return self.source_code[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source_code):
            return "\0"
        return self.source_code[self.current + 1]

    def _handle_strings(self):
        while self._peek() not in STRING_IDENTIFIERS and not self._is_end():
            if self._peek() == "\n":
                self.line += 1
            self._advance()

        if self._is_end():
            Logger.error(
                error_type=ErrorType.LexicalError,
                line=self.line,
                message="Unterminated string",
            )
            return

        # Move ahead of final quote
        self._advance()

        # Trim quotes
        value = self.source_code[self.start + 1 : self.current - 1]
        self._add_token(token_type=TokenType.STRING, literal=value)

    def _handle_numbers(self):
        while self._peek().isdigit():
            self._advance()

        if self._peek() == "." and self._peek_next().isdigit():
            # Consume . to move to the digit
            self._advance()
            while self._peek().isdigit():
                self._advance()

        number = float(self.source_code[self.start : self.current])

        self._add_token(token_type=TokenType.NUMBER, literal=number)

    def _is_alpha(self, char: str):
        return char in VALID_IDENTIFIER_CHARACTERS

    def _is_alphanumeric(self, char: str):
        return char in VALID_IDENTIFIER_CHARACTERS or char.isdigit()

    def _handle_identifiers(self):
        while self._is_alphanumeric(self._peek()):
            self._advance()
        code = self.source_code[self.start : self.current]
        token_type = KEYWORDS.get(code)

        if token_type == None:
            token_type = TokenType.IDENTIFIER

        self._add_token(token_type=token_type)
