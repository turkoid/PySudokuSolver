from __future__ import annotations
from sudoku.dependencies import *
from sudoku.sudoku import Cell
from typing import *


class CellAction(object):
    def __init__(self, cell: Cell, old: Optional[Set[int]] = None, new: Optional[Set[int]] = None) -> None:
        self.cell = cell
        self.old = old if old else cell.old_candidates
        self.new = new if new else cell.candidates

    def __str__(self) -> str:
        pass


class Action(object):
    def __init__(self, op: ActionOperation, cells: Iterable[Cell], values: Set[int]) -> None:
        self.op = op
        self.cells = cells
        self.values = values
        self.cell_actions = [CellAction(c) for c in cells if c.candidates_changed()]

    def __str__(self) -> str:
        pass


class Step(object):
    def __init__(self, technique: Technique, cells: Iterable[Cell], values: Set[int],
                 actions: Optional[Iterable[Action]] = None) -> None:
        self.technique = technique
        self.cells = list(cells)
        self.values = set(values)
        self.actions = list(actions) if actions else None

    def __str__(self) -> str:
        pass

    def summary(self) -> str:
        pass

    def description(self) -> str:
        pass

    def action_summary(self) -> str:
        pass

    def actions_detail(self) -> str:
        pass


def action_solve(cell: Cell) -> Action:
    return Action(ActionOperation.SOLVE, [cell], {cell.value})


def action_remove(cells: Iterable[Cell], candidates: Set[int]) -> Action:
    return Action(ActionOperation.REMOVE, cells, candidates)


def action_exclusive(cells: Iterable[Cell], candidates: Set[int]) -> Action:
    return Action(ActionOperation.EXCLUSIVE, cells, candidates)


def action_equal(cell: Cell, candidates: Set[int]) -> Action:
    return Action(ActionOperation.EQUAL, [cell], candidates)


def step_populate(cells: Iterable[Cell], candidates: Set[int]) -> Step:
    cells = list(cells)
    return Step(
        Technique(TechniqueArchetype.POPULATE, len(cells)),
        cells,
        candidates,
        [action_equal(c, c.candidates) for c in cells])
