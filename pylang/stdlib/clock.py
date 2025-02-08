import time
from typing import List

from interpreter.callable import Callable


class ClockCallable(Callable):
    def call(self, interpreter: "Interpreter", arguments: List[object]):
        return time.time()

    def arity(self):
        return 0

    def __str__(self):
        return "<native fn>clock"
