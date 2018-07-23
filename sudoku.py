import re
import numpy as np
from collections import namedtuple
import itertools as it

Point = namedtuple("Point", "x y")
Dimension = namedtuple("Dimension", "width height")


class Sudoku(object):
    DEFAULT_BOARD_DIMENSION = Dimension(3, 3)

    def __init__(self, initial, dimension=DEFAULT_BOARD_DIMENSION):
        self.initial = list(("0" * self.length**2) if initial is None else re.sub("\n| ", "", initial).upper())
        self.dimension = dimension
        self.length = dimension.width * dimension.height

        self.cells = [Cell(dimension, self.index_to_coord(i), value) for i, value in enumerate(initial)]
        self.board = np.array(self.cells).reshape(self.length, self.length)

        self.rows = [self.row(y).tolist() for y in range(0, self.length)]
        self.columns = [self.column(x).tolist() for x in range(0, self.length)]
        self.squares = [self.square(Point(x, y)).tolist()
                        for y in range(0, dimension.height)
                        for x in range(0, dimension.width)]

        self.populate_candidates()

    def reset(self):
        for cell, value in zip(self.cells, list(self.initial)):
            cell.value = value

    def cell(self, coord):
        return self.board[coord.y][coord.x]

    def column(self, x, flatten=True):
        cells = self.board[:, x]
        return cells.flatten() if flatten else cells

    def row(self, y):
        return self.board[y]

    def square(self, coord, flatten=True):
        cells = self.board[
                coord.y * self.dimension.width:(coord.y + 1) * self.dimension.width,
                coord.x * self.dimension.height:(coord.x + 1) * self.dimension.height]
        return cells.flatten() if flatten else cells

    def related_cells(self, parent, relations=["square", "row", "column"], filter=None):
        cells = set()
        if "square" in relations:
            cells |= set(self.square(parent.square))
        if "row" in relations:
            cells |= set(self.row(parent.location.y))
        if "column" in relations:
            cells |= set(self.column(parent.location.x))
        cells -= {parent}
        return list(cells) if filter is None else [c for c in cells if filter(c)]

    def populate_candidates(self):
        for cell in [c for c in self.cells if c.value == 0]:
            cell.value = None
            cell.candidates = set(range(1, 10)).difference(
                (rc.value for rc in self.related_cells(cell, filter=lambda c: c.value != 0)))

    @staticmethod
    def remove_candidates_from_cells(cells, candidates):
        if not candidates: return False
        cells = [c for c in cells if c.value == 0 and c.candidates and not c.candidates.isdisjoint(candidates)]
        for cell in cells: cell.candidates -= candidates
        return len(cells) > 0

    @staticmethod
    def is_same_column(cells):
        return not cells or [c.location.x for c in cells].count(cells[0].location.x) == len(cells)

    @staticmethod
    def is_same_row(cells):
        return not cells or [c.location.y for c in cells].count(cells[0].location.y) == len(cells)

    @staticmethod
    def is_same_square(cells):
        return not cells or [c.square for c in cells].count(cells[0].square) == len(cells)
    
    def solve(self):
        techniques = [
            self.check_sole_candidates,
            self.check_unique_candidates,
            self.check_subsets,
            # self.check_blocking_subsets,
            # self.check_x_wing
        ]
        changed = True
        while changed:
            changed = False
            for technique in techniques:
                changed = changed or technique()

    def check_sole_candidates(self):
        cells = [c for c in self.cells if c.value == 0 and len(c.candidates) == 1]
        changed = len(cells) > 0
        for cell in cells:
            cell.value = next(iter(cell.candidates))
            Sudoku.remove_candidates_from_cells(self.related_cells(cell), {cell.value})
            print("sole_candidate")
        return changed

    def check_unique_candidates(self):
        changed = False
        cells = [c for c in self.cells if c.value == 0]
        for cell in cells:
            for relation in ["square", "row", "column"]:
                unique_candidates = cell.candidates.difference(
                    *[rc.candidates for rc in self.related_cells(cell, [relation], filter=lambda c: c.value == 0)])
                if len(unique_candidates) == 1:
                    cell.value = next(iter(unique_candidates))
                    Sudoku.remove_candidates_from_cells(self.related_cells(cell), {cell.value})
                    changed = True
                    break
        return changed

    def check_subsets(self):
        changed = False
        for relation in ["square", "row", "column"]:
            cell_groups = [[c for c in grp if c.value == 0] for grp in (
                self.squares if relation == "square"
                else self.rows if relation == "row"
                else self.columns
            )]
            for cells in cell_groups:
                for combo_length in range(2, len(cells) - 1):
                    for combo in it.combinations(cells, combo_length):
                        other_cells = [c for c in cells if c not in combo]
                        candidates = set().union(*[c.candidates for c in combo])
                        candidates -= set().union(*[c.candidates for c in other_cells])
                        if len(candidates) == combo_length:
                            changed = Sudoku.remove_candidates_from_cells(
                                combo, candidates.symmetric_difference(
                                    set().union(*[c.candidates for c in combo])
                                )) or changed
                            changed = Sudoku.remove_candidates_from_cells(other_cells, candidates) or changed
                            blocking_relation = None
                            if relation == "square":
                                if Sudoku.is_same_column(combo):
                                    blocking_relation = "column"
                                elif Sudoku.is_same_row(combo):
                                    blocking_relation = "row"
                            elif Sudoku.is_same_square(combo):
                                blocking_relation = "square"
                            if blocking_relation is not None:
                                changed = Sudoku.remove_candidates_from_cells(self.related_cells(
                                    combo[0], [blocking_relation], filter=lambda c: c.value == 0 and c not in combo), candidates
                                ) or changed
        return changed

    def __str__(self):
        column_labels = list()
        column_labels.append("   ")
        for x in range(0, self.length):
            if x % self.dimension.height == 0: column_labels.append("  ")
            column_labels.append("{} ".format(chr(ord("A") + x)))
        column_labels.append("   \n")

        line = list()
        line.append("   ")
        line.extend(["+" if i % 2 == 0 else "-" * (self.dimension.height * 2 + 1)
                    for i in range(0, self.dimension.width * 2)])
        line.append("+   \n")

        buffer = list()
        buffer.extend(column_labels)
        for y, row in enumerate(self.board):
            if y % self.dimension.width == 0: buffer.extend(line)
            buffer.append("{: >2} ".format(y + 1))
            for x, cell in enumerate(row):
                if x % self.dimension.height == 0: buffer.append("| ")
                buffer.append("{} ".format(str(cell)))
            buffer.append("| {: <2}\n".format(y + 1))
        buffer.extend(line)
        buffer.extend(column_labels)

        return "".join(buffer)

    def print(self):
        print(str(self))

    def index_to_coord(self, index):
        return Point(index % self.length, int(index / self.length))

    def coord_to_index(self, coord):
        return coord.y * self.length + coord.x


class Cell(object):
    MAX_CELL_VALUE = 25
    CELL_VALUE_MAP = dict(list(zip(
        range(0, MAX_CELL_VALUE + 1),
        [" "] + [str(i) for i in range(1, 10)] + [chr(code) for code in range(ord("A"), ord("A") + MAX_CELL_VALUE - 9)]
    )))

    def __init__(self, board_dimension, location, value=None):
        self.board_dimension = board_dimension
        self.location = location
        self.square = Point(int(location.x / board_dimension.height), int(location.y / board_dimension.width))
        self.candidates = None
        self.value = value

    def __str__(self):
        return " " if self.value == 0 else Cell.CELL_VALUE_MAP[self.value]

    def __repr__(self):
        return "Cell({}, {}, {})".format(self.board_dimension, self.location, self.value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value is None:
            self._value = 0
        elif isinstance(value, str) and not (ord("0") <= ord(value) <= ord("9")):
            self._value = ord(value) - ord("A") + 10
        else:
            self._value = int(value)
        self.candidates = {} if self.value == 0 else {self.value}


initial = (
    "000005790"
    "000800006"
    "005609403"
    "400003900"
    "090000210"
    "080094300"
    "050001070"
    "308002140"
    "020900605"
)
initial = "070004000869000000000000010000010007080009600002057040958003000000001200300000789"
#initial = "090600800000503400807000610000050007000790100000006300070000020040000000203061004"
#initial = "000000000200601005004203900031000850600705009085000470006509200400106007000000000"  # 4831
puzzle = Sudoku(initial)
puzzle.print()
puzzle.solve()
puzzle.print()

