from sudoku.enums import ActionOperation


class Step(object):
    def __init__(self, technique, cells, values):
        self.technique = technique
        self.cells = cells
        self.values = values
        self.actions = []

    def __str__(self):
        pass

    def summary(self):
        pass

    def description(self):
        pass

    def summary_action(self):
        pass

    def actions(self):
        pass


class Action(object):
    def __init__(self, op, cells, values):
        self.op = op
        self.cells = cells
        self.values = values

    @staticmethod
    def solve(cell, value):
        return Action(ActionOperation.SOLVE, cell, value)

    @staticmethod
    def remove(cells, candidates):
        return Action(ActionOperation.REMOVE, cells, candidates)

    @staticmethod
    def exclusive(cells, candidates):
        return Action(ActionOperation.EXCLUSIVE, cells, candidates)

    @staticmethod
    def equal(cell, candidates):
        return Action(ActionOperation.EQUAL, cell, candidates)

    def __str__(self):
        pass
