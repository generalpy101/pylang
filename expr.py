from abc import ABC, abstractmethod
from dataclasses import dataclass

from tokens import Token


# Visitor interface
class ExprVisitor(ABC):

    @abstractmethod
    def visit_binary(self, expr: "Binary"):
        pass

    @abstractmethod
    def visit_grouping(self, expr: "Grouping"):
        pass

    @abstractmethod
    def visit_literal(self, expr: "Literal"):
        pass

    @abstractmethod
    def visit_unary(self, expr: "Unary"):
        pass


# Base Expr class
class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: ExprVisitor):
        pass


@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_binary(self)


@dataclass
class Grouping(Expr):
    expression: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_grouping(self)


@dataclass
class Literal(Expr):
    value: object

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_literal(self)


@dataclass
class Unary(Expr):
    operator: Token
    right: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_unary(self)
