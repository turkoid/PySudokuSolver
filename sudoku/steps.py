from sudoku.dependencies import Technique, ActionOperation
from typing import *
from sudoku.sudoku import Cell


class Action(object):
    def __init__(self, op: ActionOperation, cells: Iterable[Cell], values: Set[int]) -> None:
        self.op = op
        self.cells = cells
        self.values = values

    @staticmethod
    def solve(cell: Cell) -> "Action":
        return Action(ActionOperation.SOLVE, [cell])

    @staticmethod
    def remove(cells: Iterable[Cell], candidates: Set[int]) -> "Action":
        return Action(ActionOperation.REMOVE, cells, candidates)

    @staticmethod
    def exclusive(cells: Iterable[Cell], candidates: Set[int]) -> "Action":
        return Action(ActionOperation.EXCLUSIVE, cells, candidates)

    @staticmethod
    def equal(cell: Cell, candidates: Set[int]) -> "Action":
        return Action(ActionOperation.EQUAL, [cell], candidates)

    def __str__(self) -> str:
        pass


class Step(object):
    def __init__(self, technique: Technique, cells: Iterable[Cell], values: Set[int],
                 actions: Optional[List[Action]] = None) -> None:
        self.technique = technique
        self.cells = cells
        self.values = values
        self.actions = [] if actions is None else actions

    def __str__(self) -> str:
        pass

    def summary(self) -> str:
        pass

    def description(self) -> str:
        pass

    def actions_detail(self) -> str:
        pass
