from enum import Enum


class CellRelation(Enum):
    BOX = 0,
    ROW = 1,
    COLUMN = 2

    @classmethod
    def all(cls):
        return {r for r in cls}


class TechniqueArchetype(Enum):
    POPULATE = 0
    NAKED = 1
    HIDDEN = 2
    POINTING = 3
    CLAIMING = 4
    FISH = 5
    WING = 6


class ActionOperation(Enum):
    SOLVE = 0
    REMOVE = 1
    EXCLUSIVE = 2
    EQUAL = 3