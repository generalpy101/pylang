from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from lexer.tokens import Token


# Visitor interface
class ExprVisitor(ABC):
    @abstractmethod
    def visit_assign(self, expr: "Assign"):
        pass

    @abstractmethod
    def visit_binary(self, expr: "Binary"):
        pass

    @abstractmethod
    def visit_call(self, expr: "Call"):
        pass

    @abstractmethod
    def visit_grouping(self, expr: "Grouping"):
        pass

    @abstractmethod
    def visit_literal(self, expr: "Literal"):
        pass

    @abstractmethod
    def visit_logical(self, expr: "Logical"):
        pass

    @abstractmethod
    def visit_unary(self, expr: "Unary"):
        pass

    @abstractmethod
    def visit_variable(self, expr: "Variable"):
        pass


# Base Expr class
class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: ExprVisitor):
        pass

    def __hash__(self):
        return hash(str(self))


@dataclass(eq=False)
class Assign(Expr):
    name: Token
    value: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_assign(self)


@dataclass(eq=False)
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_binary(self)


@dataclass(eq=False)
class Call(Expr):
    callee: Expr
    paren: Token
    arguments: List[Expr]

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_call(self)


@dataclass(eq=False)
class Grouping(Expr):
    expression: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_grouping(self)


@dataclass(eq=False)
class Literal(Expr):
    value: object

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_literal(self)


@dataclass(eq=False)
class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_logical(self)


@dataclass(eq=False)
class Unary(Expr):
    operator: Token
    right: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_unary(self)


@dataclass(eq=False)
class Variable(Expr):
    name: Token

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_variable(self)
