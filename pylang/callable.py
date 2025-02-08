from abc import ABC, abstractmethod
from typing import List


class Callable(ABC):
    @abstractmethod
    def call(self, interpreter: "Interpreter", arguments: List[object]):
        pass

    @abstractmethod
    def arity(self):
        pass

    @abstractmethod
    def __str__(self):
        pass
