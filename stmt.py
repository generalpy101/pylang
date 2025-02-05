from abc import ABC, abstractmethod
from dataclasses import dataclass

from expr import Expr


# Visitor interface
class StmtVisitor(ABC):

    @abstractmethod
    def visit_expression_stmt(self, expr: "ExpressionStmt"):
        pass

    @abstractmethod
    def visit_print_stmt(self, expr: "PrintStmt"):
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
