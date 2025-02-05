from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from expr import Expr
from tokens import Token


# Visitor interface
class StmtVisitor(ABC):

    @abstractmethod
    def visit_expression_stmt(self, expr: "ExpressionStmt"):
        pass

    @abstractmethod
    def visit_print_stmt(self, expr: "PrintStmt"):
        pass

    @abstractmethod
    def visit_var_stmt(self, expr: "VarStmt"):
        pass

    @abstractmethod
    def visit_block_stmt(self, expr: "BlockStmt"):
        pass

    @abstractmethod
    def visit_if_stmt(self, expr: "IfStmt"):
        pass
    
    @abstractmethod
    def visit_while_stmt(self, expr: "WhileStmt"):
        pass

# Base Expr class
class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: StmtVisitor):
        pass


@dataclass
class ExpressionStmt(Stmt):
    expression: Expr

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_expression_stmt(self)


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
class BlockStmt(Stmt):
    statements: List[Stmt]

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_block_stmt(self)


@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_if_stmt(self)
    
    
@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: Stmt

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_while_stmt(self)