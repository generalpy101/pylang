from abc import ABC, abstractmethod
from ast_pylang.expr import Expr, Variable
from dataclasses import dataclass
from typing import List

from lexer.tokens import Token


# Visitor interface
class StmtVisitor(ABC):
    @abstractmethod
    def visit_block_stmt(self, stmt: "BlockStmt"):
        pass

    @abstractmethod
    def visit_expression_stmt(self, stmt: "ExpressionStmt"):
        pass

    @abstractmethod
    def visit_function_stmt(self, stmt: "FunctionStmt"):
        pass

    @abstractmethod
    def visit_if_stmt(self, stmt: "IfStmt"):
        pass

    @abstractmethod
    def visit_print_stmt(self, stmt: "PrintStmt"):
        pass

    @abstractmethod
    def visit_var_stmt(self, stmt: "VarStmt"):
        pass

    @abstractmethod
    def visit_while_stmt(self, stmt: "WhileStmt"):
        pass

    @abstractmethod
    def visit_return_stmt(self, stmt: "ReturnStmt"):
        pass

    @abstractmethod
    def visit_class_stmt(self, stmt: "ClassStmt"):
        pass


# Base Expr class
class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: StmtVisitor):
        pass


@dataclass
class BlockStmt(Stmt):
    statements: List[Stmt]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_block_stmt(self)


@dataclass
class ExpressionStmt(Stmt):
    expression: Expr

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_expression_stmt(self)


@dataclass
class FunctionStmt(Stmt):
    name: Token
    params: List[Token]
    body: List[Stmt]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_function_stmt(self)


@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_if_stmt(self)


@dataclass
class PrintStmt(Stmt):
    expression: Expr

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_print_stmt(self)


@dataclass
class VarStmt(Stmt):
    name: Token
    initializer: Expr

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_var_stmt(self)


@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: Stmt

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_while_stmt(self)


@dataclass
class ReturnStmt(Stmt):
    keyword: Token
    value: Expr

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_return_stmt(self)


@dataclass
class ClassStmt(Stmt):
    name: Token
    superclass: (
        Variable  # Superclass will be an variable in the scope so evaluate it as such
    )
    methods: List[FunctionStmt]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_class_stmt(self)
