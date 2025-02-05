import errno
import sys
from io import TextIOWrapper
from typing import Dict, Tuple


def define_type(
    file: TextIOWrapper, base_class_name: str, class_name: str, fields: str
):
    field_declaractions = ""
    for field in fields:
        name, type = field
        field_declaractions += f"{name}: {type}\n    "

    output_string = f"""
@dataclass
class {class_name}({base_class_name}):
    {field_declaractions}
    
    def accept(self, visitor: {base_class_name}Visitor):
        return visitor.visit_{class_name.lower()}(self)
    """
    file.write(output_string)


def define_ast(
    output_directory: str, base_name: str, types: Dict[str, Tuple[Tuple[str]]]
):
    output_path = f"{output_directory}/{base_name.lower()}.py"

    with open(output_path, "w") as output_file:
        # Handle visitor interface part
        visitor_method_format = """
        @abstractmethod
        def visit_{type_name}(self, expr: '{type}'):
            pass
    """
        visitor_methods = [
            visitor_method_format.format(type_name=type.lower(), type=type)
            for type in types.keys()
        ]
        visitor_interface = f"""
# Visitor interface
class {base_name}Visitor(ABC):
    {''.join(visitor_methods)}
        """

        # Handle initial contents + interface (including writing to file)
        initial_contents = f"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from tokens import Token

{visitor_interface}

# Base Expr class
class {base_name}(ABC):
    @abstractmethod
    def accept(self, visitor: {base_name}Visitor):
        pass
"""
        output_file.write(initial_contents)
        for class_name, fields in types.items():
            define_type(
                file=output_file,
                base_class_name=base_name,
                class_name=class_name,
                fields=fields,
            )


def main():
    if len(sys.argv) != 2:
        print("Usage: python {__name__}.py <output_directory>")
        sys.exit(errno.EINVAL)
    output_dir = sys.argv[1]

    define_ast(
        output_directory=output_dir,
        base_name="Expr",
        types={
            "Assign": (("name", "Token"), ("value", "Expr")),
            "Binary": (("left", "Expr"), ("operator", "Token"), ("right", "Expr")),
            "Grouping": (("expression", "Expr"),),
            "Literal": (("value", "object"),),
            "Unary": (("operator", "Token"), ("right", "Expr")),
            "Variable": (("name", "Token"),),
        },
    )

    define_ast(
        output_directory=output_dir,
        base_name="Stmt",
        types={
            "Block": (("statements", "List[Stmt]"),),
            "Expression": (("expression", "Expr"),),
            "Print": (("expression", "Expr"),),
            "Var": (("name", "Token"), ("initializer", "Expr")),
        },
    )


if __name__ == "__main__":
    main()
