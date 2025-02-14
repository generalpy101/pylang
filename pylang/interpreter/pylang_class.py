from typing import Dict, List

from interpreter.callable import Callable
from interpreter.pylang_function import PylangFunction
from interpreter.pylang_instance import PylangInstance


class PylangClass(Callable):
    def __init__(
        self, name: str, superclass: "PylangClass", methods: Dict[str, PylangFunction]
    ):
        self.name = name
        self.methods = methods
        self.superclass = superclass

    def call(self, interpreter: "Interpreter", arguments: List[object]):
        instance = PylangInstance(self)
        initializer = self.find_method("init")
        if initializer is not None:
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    def arity(self):
        initializer = self.find_method("init")
        if initializer is not None:
            return initializer.arity()
        return 0

    def find_method(self, name: str) -> PylangFunction | None:
        if name in self.methods:
            return self.methods[name]

        if self.superclass is not None:
            return self.superclass.find_method(name)
        return None

    def __str__(self):
        return self.name
