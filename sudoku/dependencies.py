from __future__ import annotations
from typing import Set, Optional
from enum import Enum
from dataclasses import dataclass


class CellRelation(Enum):
    BOX = 0,
    ROW = 1,
    COLUMN = 2

    @classmethod
    def all(cls) -> Set[CellRelation]:
        return {r for r in cls}


class TechniqueArchetype(Enum):
    POPULATE = 0
    NAKED = 1
    HIDDEN = 2
    LOCKED = 3
    FISH = 4
    WING = 5


class ArchetypeVariation(Enum):
    BOX = 0
    ROW = 1
    COLUMN = 2


class ActionOperation(Enum):
    SOLVE = 0
    REMOVE = 1
    EXCLUSIVE = 2
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
    variation: Optional[ArchetypeVariation] = None


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
