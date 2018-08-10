from __future__ import annotations
from typing import *
from enum import Enum
from dataclasses import dataclass
import sudoku.puzzle as sudoku


class CellRelation(Enum):
    BOX = 0,
    ROW = 1,
    COLUMN = 2


class TechniqueArchetype(Enum):
    POPULATE = 0
    NAKED = 1
    HIDDEN = 2
    LOCKED = 3
    FISH = 4
    WING = 5


class ActionOperation(Enum):
    SOLVE = 0
    DIFFERENCE = 1
    INTERSECTION = 2
    EQUAL = 3


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class Dimension:
    width: int
    height: int


@dataclass(frozen=True)
class Technique:
    type: TechniqueArchetype
    size: int
    source_relation: Optional[Set[CellRelation]] = None
    target_relation: Optional[Set[CellRelation]] = None


@dataclass(frozen=True)
class Fish:
    size: int
    cells: Iterable[sudoku.Cell]


@dataclass(frozen=True)
class Wing:
    pivot: sudoku.Cell
    cells: Iterable[sudoku.Cell]


# the default dimension of a single box (not the board)
DEFAULT_BOX_SIZE = Dimension(3, 3)
# The max is 25 only because of column labeling (A-Z). If i didn't output to only console, this limit could be increased
MAX_CELL_VALUE = 25
# Dictionary from cell value to single character (after 9, alpha characters are used)
CELL_VALUE_MAP = dict(list(zip(
    range(0, MAX_CELL_VALUE + 1),
    [" "] + [str(i) for i in range(1, 10)] + [chr(code) for code in range(ord("A"), ord("A") + MAX_CELL_VALUE - 9)]
)))
NO_CANDIDATES = frozenset([])
ALL_RELATIONS = {r for r in CellRelation}
TUPLE_SIZE = {
    1: "Single",
    2: "Pair",
    3: "Triple",
    4: "Quadruple"
}
FISH_SIZE = {
    2: "X-Wing",
    3: "Swordfish",
    4: "Jellyfish"
}
RELATION = {
    CellRelation.BOX: "Box",
    CellRelation.ROW: "Row",
    CellRelation.COLUMN: "Column"
}

ModifyOperation = Callable[[Set[int], Tuple[Iterable[int], ...]], Set[int]]
