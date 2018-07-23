import re
import numpy as np
from collections import namedtuple
import itertools as it

Point = namedtuple("Point", "x y")
Dimension = namedtuple("Dim", "width height")
CellRectangle = namedtuple("CellRect", "top_left top_right bottom_left bottom_right")


class Sudoku(object):
    DEFAULT_BOARD_SIZE = Dimension(3, 3)

    def __init__(self, initial, size=DEFAULT_BOARD_SIZE):
        self.initial = list(("0" * self.length**2) if initial is None else re.sub("\n| ", "", initial).upper())
        self.size = size
        self.length = size.width * size.height

        self.cells = [Cell(size, self.index_to_coord(i), value) for i, value in enumerate(initial)]
        self.board = np.array(self.cells).reshape(self.length, self.length)

        self.rows = [self.row(y).tolist() for y in range(0, self.length)]
        self.columns = [self.column(x).tolist() for x in range(0, self.length)]
        self.squares = [self.square(Point(x, y)).tolist()
                        for y in range(0, size.height)
                        for x in range(0, size.width)]

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
                coord.y * self.size.width:(coord.y + 1) * self.size.width,
                coord.x * self.size.height:(coord.x + 1) * self.size.height]
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
            cell.candidates = set(range(1,  self.length + 1)).difference(
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
            self.solve_candidates,
            self.solve_subsets,
            self.solve_advanced
        ]
        changed = True
        while changed:
            changed = False
            for technique in techniques:
                changed = changed or technique()

    def solve_candidates(self):
        changed = False
        cells = [c for c in self.cells if c.value == 0]
        for cell in cells:
            if len(cell.candidates) == 1:
                candidates = cell.candidates
            else:
                for relation in ["square", "row", "column"]:
                    candidates = cell.candidates.difference(
                        *[rc.candidates for rc in self.related_cells(cell, [relation], filter=lambda c: c.value == 0)])
                    if len(candidates) == 1: break
            if len(candidates) == 1:
                cell.value = next(iter(candidates))
                Sudoku.remove_candidates_from_cells(self.related_cells(cell), {cell.value})
                changed = True
        return changed

    def solve_subsets(self):
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

    def solve_advanced(self):
        changed = False

        rectangles = [
            CellRectangle(
                tl,
                self.cell(Point(br.location.x, tl.location.y)),
                self.cell(Point(tl.location.x, br.location.y)),
                br
            )
            for tl in self.cells if (
                tl.value == 0
                and tl.square.x < self.size.width - 1 and tl.square.y < self.size.height - 1
            )
            for br in self.cells if (
                br.value == 0
                and br.location.x > tl.location.x and br.location.y > tl.location.y
                and br.square.x > tl.square.x and br.square.y > tl.square.x
            ) if (
                self.cell(Point(tl.location.x, br.location.y)).value == 0
                and self.cell(Point(br.location.x, tl.location.y)).value == 0
            )
        ]

        for rect in rectangles:
            row_cells = [c for c in self.row(rect.top_left.location.y) if c.value == 0 and c not in rect]
            row_cells.extend([c for c in self.row(rect.bottom_right.location.y) if c.value == 0 and c not in rect])
            col_cells = [c for c in self.column(rect.top_left.location.x) if c.value == 0 and c not in rect]
            col_cells.extend([c for c in self.column(rect.bottom_right.location.x) if c.value == 0 and c not in rect])
            for relation in ["row", "column"]:
                candidates = Cell.CANDIDATES.intersection(*[c.candidates for c in rect])
                candidates -= set().union(*[c.candidates for c in (row_cells if relation == "row" else col_cells)])
                changed = self.remove_candidates_from_cells(
                    (col_cells if relation == "row" else row_cells), candidates
                ) or changed
        return changed

    def __str__(self):
        column_labels = list()
        column_labels.append("   ")
        for x in range(0, self.length):
            if x % self.size.height == 0: column_labels.append("  ")
            column_labels.append("{} ".format(chr(ord("A") + x)))
        column_labels.append("   \n")

        line = list()
        line.append("   ")
        line.extend(["+" if i % 2 == 0 else "-" * (self.size.height * 2 + 1)
                    for i in range(0, self.size.width * 2)])
        line.append("+   \n")

        buffer = list()
        buffer.extend(column_labels)
        for y, row in enumerate(self.board):
            if y % self.size.width == 0: buffer.extend(line)
            buffer.append("{: >2} ".format(y + 1))
            for x, cell in enumerate(row):
                if x % self.size.height == 0: buffer.append("| ")
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
    CANDIDATES = set(range(1, MAX_CELL_VALUE + 1))
    CELL_VALUE_MAP = dict(list(zip(
        range(0, MAX_CELL_VALUE + 1),
        [" "] + [str(i) for i in CANDIDATES] + [chr(code) for code in range(ord("A"), ord("A") + MAX_CELL_VALUE - 9)]
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


data = (
    "000005790"
    "000800006"
    "005609403"
    "400003900"
    "090000210"
    "080094300"
    "050001070"
    "308002140"
    "020900605"
)  # from app
data = "070004000869000000000000010000010007080009600002057040958003000000001200300000789"  # from app
data = "090600800000503400807000610000050007000790100000006300070000020040000000203061004"  # from app
data = "000000000200601005004203900031000850600705009085000470006509200400106007000000000"  # 4831 x-wing
data = "000000000000000805000071000000000007005090081007008593008023070039005000071060004"  # 3096 xy-wing

puzzle = Sudoku(data)
puzzle.print()
puzzle.solve()
puzzle.print()

