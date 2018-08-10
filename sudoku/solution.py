from __future__ import annotations
from sudoku.dependencies import *
import sudoku.puzzle as sudoku
from typing import *


def plural(w, suffix, count):
    return w if count == 1 else w + suffix


def plural_s(count):
    return plural("", "s", count)


def print_candidates(candidates):
    return ", ".join([str(v) for v in candidates])


def print_cells(cells):
    return ", ".join([c.var_to_string("location") for c in cells])


class CellAction(object):
    def __init__(self, cell: sudoku.Cell, old: Optional[Set[int]] = None, new: Optional[Set[int]] = None) -> None:
        self.cell = cell
        self.old = old if old else cell.old_candidates
        self.new = new if new else cell.candidates
        self.op = "+" if len(self.new) > len(self.old) else "-"
        self.change = self.old.symmetric_difference(self.new)

    def __str__(self) -> str:
        return "Candidate{s} {candidates} {op} cell ( {cell} )".format(
            s=plural_s(len(self.change)),
            candidates=print_candidates(self.change),
            op="added to" if self.op is "+" else "removed from",
            cell=self.cell.var_to_string("location")
        )


class Action(object):
    def __init__(self, op: ActionOperation, cells: Iterable[sudoku.Cell], values: Set[int]) -> None:
        self.op = op
        self.cells = list(cells)
        self.values = values
        self.cell_actions = [CellAction(c) for c in cells if c.candidates_changed()]

    def __str__(self) -> str:
        buffer = list()
        if self.op is ActionOperation.SOLVE:
            buffer.append("Cell ( {cell} ) solved with value {value}".format(
                cell=self.cells[0],
                value=self.cells[0].value
            ))
        elif self.op is ActionOperation.DIFFERENCE:
            buffer.append("Candidate{s} {candidates} removed from cell{s2} ( {cells} )".format(
                s=plural_s(len(self.values)),
                candidates=print_candidates(self.values),
                s2=plural_s(len(self.cells)),
                cells=print_cells(self.cells)
            ))
        elif self.op is ActionOperation.EQUAL:
            buffer.append("Cell{s} ( {cells} ) candidates set to {candidates} ".format(
                s=plural_s(len(self.cells)),
                cells=print_cells(self.cells),
                candidates=print_candidates(self.values)
            ))
        elif self.op is ActionOperation.INTERSECTION:
            buffer.append("All candidates except {candidates} removed from cell{s} ( {cells} )".format(
                candidates=print_candidates(self.values),
                s=plural_s(len(self.cells)),
                cells=print_cells(self.cells)
            ))

        for action in self.cell_actions:
            buffer.append("\n\t\t{action}".format(action=str(action)))

        return "".join(buffer)


class Step(object):
    def __init__(self, technique: Technique, cells: Iterable[sudoku.Cell], values: Set[int],
                 actions: Optional[Iterable[Action]] = None) -> None:
        self.technique = technique
        self.cells = list(cells)
        self.values = set(values)
        self.actions = list(actions) if actions else None

    def __str__(self) -> str:
        buffer = list()
        if self.technique.type is TechniqueArchetype.POPULATE:
            buffer.append("Populating all possible candidates in {size} cell{s}".format(
                size=self.technique.size,
                s=plural_s(self.technique.size)
            ))
        else:
            if self.technique.type is TechniqueArchetype.NAKED:
                type_str = "Naked "
                if self.technique.size <= len(TUPLE_SIZE):
                    type_str += TUPLE_SIZE[self.technique.size]
                else:
                    type_str += "Subset[{}]".format(self.technique.size)
            elif self.technique.type is TechniqueArchetype.HIDDEN:
                type_str = "Hidden "
                if self.technique.size <= len(TUPLE_SIZE):
                    type_str += TUPLE_SIZE[self.technique.size]
                else:
                    type_str += "Subset[{}]".format(self.technique.size)
                type_str += " in {relation} {location}".format(
                    relation=RELATION[next(iter(self.technique.source_relation))],
                    location=self.cells[0].var_to_string("box")
                    if CellRelation.BOX in self.technique.source_relation else
                    str(self.cells[0].location.x + 1) if CellRelation.COLUMN in self.technique.source_relation else
                    chr(ord("A") + self.cells[0].location.y)
                )
            elif self.technique.type is TechniqueArchetype.LOCKED:
                type_str = "Locked({}) ".format(
                    "Claiming" if self.technique.target_relation is CellRelation.BOX else "Pointing")
                if self.technique.size <= len(TUPLE_SIZE):
                    type_str += TUPLE_SIZE[self.technique.size]
                else:
                    type_str += "Subset[{}]".format(self.technique.size)
            elif self.technique.type is TechniqueArchetype.FISH:
                if self.technique.size <= len(FISH_SIZE):
                    type_str = "{} ".format(FISH_SIZE[self.technique.size])
                else:
                    type_str = "Fish[{}] ".format(self.technique.size)
            elif self.technique.type is TechniqueArchetype.WING:
                type_str = "XY-Wing "
            else:
                type_str = "{}[{}] ".format(self.technique.type, self.technique.size)
            buffer.append("{type} in cell{s} ( {cells} )".format(
                type=type_str,
                s=plural_s(self.technique.size),
                cells=print_cells(self.cells)
            ))
        for action in self.actions:
            buffer.append("\n\t{action}".format(action=str(action)))

        return "".join(buffer)

    def summary(self) -> str:
        pass

    def description(self) -> str:
        pass

    def action_summary(self) -> str:
        pass

    def actions_detail(self) -> str:
        pass


def action_solve(cell: sudoku.Cell) -> Action:
    return Action(ActionOperation.SOLVE, [cell], {cell.value})


def action_difference(cells: Iterable[sudoku.Cell], candidates: Set[int]) -> Action:
    return Action(ActionOperation.DIFFERENCE, cells, candidates)


def action_intersection(cells: Iterable[sudoku.Cell], candidates: Set[int]) -> Action:
    return Action(ActionOperation.INTERSECTION, cells, candidates)


def action_equal(cell: sudoku.Cell, candidates: Set[int]) -> Action:
    return Action(ActionOperation.EQUAL, [cell], candidates)


def step_populate(cells: Iterable[sudoku.Cell], candidates: Set[int]) -> Step:
    cells = list(cells)
    return Step(
        Technique(TechniqueArchetype.POPULATE, len(cells)),
        cells,
        candidates,
        [action_equal(c, c.candidates) for c in cells])
