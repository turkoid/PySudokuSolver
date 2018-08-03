import numpy as np
from collections import namedtuple
import itertools as it
import math
from enum import Enum


# NAMED TUPLES
Point = namedtuple("Point", "x y")
Dimension = namedtuple("Dim", "width height")
CellRectangle = namedtuple("CellRect", "top_left top_right bottom_left bottom_right")


# CONSTANTS
# the default dimension of a single square (not the board)
DEFAULT_SQUARE_SIZE = Dimension(3, 3)
# The max is 25 only because of column labeling (A-Z). If i didn't output to only console, this limit could be increased
MAX_CELL_VALUE = 25
# A constant that stores all possible candidates
ALL_CANDIDATES = set(range(1, MAX_CELL_VALUE + 1))
# Dictionary from cell value to single character (after 9, alpha characters are used)
CELL_VALUE_MAP = dict(list(zip(
    range(0, MAX_CELL_VALUE + 1),
    [" "] + [str(i) for i in range(1, 10)] + [chr(code) for code in range(ord("A"), ord("A") + MAX_CELL_VALUE - 9)]
)))


# Enum for technique archetypes
class Technique(Enum):
    NAKED = 0
    HIDDEN = 1
    POINTING = 2
    FISH = 3
    WING = 4


class Sudoku(object):
    def __init__(self, seed, size=DEFAULT_SQUARE_SIZE):
        """
        Initializes the sudoku board

        :param seed: The starting values for the board. Use the alpha equivalent for double digit numbers
        :type seed: Iterable
        :param size: Dimension of the square, not the board. Defaults to 3x3
        :type size: Dimension
        """

        self.seed = [str(v) for v in list(seed)]
        if size is None:
            # Try to determine the size of square by taking the 4th root of the seed length
            size = int(math.sqrt(math.sqrt(len(self.seed))))
            self.size = Dimension(size, size)
        else:
            self.size = size
        self.length = self.size.width * self.size.height

        # Create each cell based on the seed value
        self.cells = [
            Cell(self.cell_square(loc), loc, v)
            for loc, v in (
                (self.index_to_location(i), v)
                for i, v in it.zip_longest(range(0, self.length**2), self.seed, fillvalue=None)
            )
        ]
        self.board = np.array(self.cells).reshape(self.length, self.length)

        self.rows = [self.row(y).tolist() for y in range(0, self.length)]
        self.columns = [self.column(x).tolist() for x in range(0, self.length)]
        self.squares = [self.square(Point(x, y)).tolist()
                        for y in range(0, self.size.height)
                        for x in range(0, self.size.width)]

        self.populate_candidates()

    def reset(self):
        """
        Resets the board to the seed value

        :return:
        """

        for cell, value in zip(self.cells, self.seed):
            cell.value = value

    def index_to_location(self, index):
        """
        Converts the index in all the cells to a point

        :param index: Index within all cells
        :type index: int
        :return: The x, y location of the cell within the board
        :rtype: Point
        """

        return Point(index % self.length, int(index / self.length))

    def location_to_index(self, location):
        """
        Converts a point to the index in all the cells

        :param location: The x, y location of the cell within the board
        :type location: Point
        :return: Index within all cells
        :rtype: int
        """

        return location.y * self.length + location.x

    def cell_square(self, location):
        """
        The square the cell is in

        :param location: The x,y location of the cell
        :type location: Point
        :return: The x,y location of the square containing the cell
        :rtype: Point
        """

        return Point(int(location.x / self.size.height), int(location.y / self.size.width))

    def cell(self, location):
        """
        Returns the cell at location

        :param location: The x, y location within all the cells
        :type location: Point
        :return: The Cell
        :rtype: Cell
        """


        return self.board[location.y][location.x]

    def column(self, x, flatten=True):
        """
        The group of cells at column x

        :param x: The column index
        :type x: int
        :param flatten: Flattens the 1xN into a Nx1 array
        :type flatten: bool
        :return: Column cells
        :rtype: list
        """

        cells = self.board[:, x]
        return cells.flatten() if flatten else cells

    def row(self, y):
        """
        The group of cells at row y
        :param y: The row index
        :type y: int
        :return: Row cells
        :rtype: list
        """

        return self.board[y]

    def square(self, location, flatten=True):
        """
        The group of cells at square location

        :param location: The x,y location of the square
        :type location: Point
        :param flatten: Flattens the MxN array into a (M*N)x1 array
        :type flatten: bool
        :return: Square cells
        :rtype: list
        """

        cells = self.board[
                location.y * self.size.width:(location.y + 1) * self.size.width,
                location.x * self.size.height:(location.x + 1) * self.size.height]
        return cells.flatten() if flatten else cells

    def related_cells(self, parent, relations=["square", "row", "column"], filter=None):
        """
        The group of cells that share a relation to the parent cell

        :param parent: The cell to find its relatives
        :type parent: Cell
        :param relations: The relationships to search for
        :type relations: Iterable
        :param filter: Function used to filter out unwanted cells
        :type filter: Function
        :return: Related cells
        :rtype: list
        """

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
        """
        Populates all cells with no value with possible candidates

        :return:
        """

        for cell in [c for c in self.cells if c.value is None]:
            cell.value = None
            cell.candidates = set(range(1,  self.length + 1)).difference(
                (rc.value for rc in self.related_cells(cell, filter=lambda c: c.value is not None)))

    @staticmethod
    def remove_candidates_from_cells(cells, candidates):
        if not candidates: return False
        cells = [c for c in cells if c.value is None and c.candidates and not c.candidates.isdisjoint(candidates)]
        for cell in cells: cell.candidates -= candidates
        return len(cells) > 0

    @staticmethod
    def is_same_column(cells):
        """
        Test to see if all cells are in the same column

        :param cells: Cells to test
        :type cells: list
        :return: True if same column, false otherwise
        :rtype: bool
        """

        return not cells or [c.location.x for c in cells].count(cells[0].location.x) == len(cells)

    @staticmethod
    def is_same_row(cells):
        """
        Test to see if all cells are in the same row

        :param cells: Cells to test
        :type cells: list
        :return: True if same row, false otherwise
        :rtype: bool
        """

        return not cells or [c.location.y for c in cells].count(cells[0].location.y) == len(cells)

    @staticmethod
    def is_same_square(cells):
        """
        Test to see if all cells are in the same square

        :param cells: Cells to test
        :type cells: list
        :return: True if same square, false otherwise
        :rtype: bool
        """

        return not cells or [c.square for c in cells].count(cells[0].square) == len(cells)

    def solve(self):
        """
        Attempts to solve the puzzle using common techniques

        :return:
        """
        before = str(self)
        techniques = [
            self.solve_singles,
            self.solve_subsets,
            self.solve_fish,
            self.solve_wings,
        ]
        while True:
            changed = False
            for technique in techniques:
                changed = changed or technique()
            if not changed: break

        after = str(self)
        # prints a side by side of before and after board
        for before_line, after_line in zip(before.split("\n"), after.split("\n")):
            print("%s   %s" % (before_line, after_line))

    def solve_singles(self):
        """
        This technique finds naked singles and hidden singles

        http://hodoku.sourceforge.net/en/tech_singles.php

        Naked single - Cell contains exactly one candidate
        Hidden single - The cell within the related cells can only contain this candidate

        :return: True if changes where made to any cell
        :rtype: bool
        """

        changed = False
        cells = [c for c in self.cells if c.value is None]
        for cell in cells:
            if len(cell.candidates) == 1:
                candidates = cell.candidates
            else:
                for relation in ["square", "row", "column"]:
                    candidates = cell.candidates.difference(
                        *[rc.candidates for rc in self.related_cells(cell, [relation], filter=lambda c: c.value is None)])
                    if len(candidates) == 1: break
            if len(candidates) == 1:
                cell.value = next(iter(candidates))
                Sudoku.remove_candidates_from_cells(self.related_cells(cell), {cell.value})
                changed = True
        return changed

    def solve_subsets(self):
        """
        This technique finds naked, hidden, and blocking subsets

        http://hodoku.sourceforge.net/en/tech_hidden.php
        http://hodoku.sourceforge.net/en/tech_naked.php

        Naked subset - The subset of cells containing only these combinations of candidates. The number of found
        candidates equals the subset size. The number of all candidates in the subsets has to equal the subset size.
        Hidden subset - Similar to naked subset, except the number of all candidates does not have to equal the subset
        size
        Blocking subset - A special variation of either naked or hidden subsets. When the subset is the same row, column
        or square, then the related cells cannot contain the subsets' candidates

        :return: True if changes where made to any cell
        :rtype: bool
        """

        changed = False
        for relation in ["square", "row", "column"]:
            # this is filtering the multi-dimensional array of rows, columns, or squares so that each sub-array contains
            # only cells with no value set
            cell_groups = [[c for c in grp if c.value is None] for grp in (
                self.squares if relation == "square"
                else self.rows if relation == "row"
                else self.columns
            )]
            for cells in cell_groups:
                # we only check for subsets of at least size 2 and 1 less then the total number cells
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
                                    combo[0], [blocking_relation], filter=lambda c: c.value is None and c not in combo
                                ), candidates) or changed
        return changed

    def solve_fish(self):
        """
        Uses the fish solving technique

        http://hodoku.sourceforge.net/en/tech_fishb.php

        X-Wing - an x-wing is a special type of fish
        Swordfish - not yet implemented

        :return: True if changes where made to any cell
        :rtype: bool
        """

        changed = False

        # finds all groups of 4 non-valued cells that form a rectangle
        rectangles = [
            CellRectangle(
                tl,
                self.cell(Point(br.location.x, tl.location.y)),
                self.cell(Point(tl.location.x, br.location.y)),
                br
            )
            for tl in self.cells if (
                tl.value is None
                and tl.square.x < self.size.width - 1 and tl.square.y < self.size.height - 1
            )
            for br in self.cells if (
                br.value is None
                and br.location.x > tl.location.x and br.location.y > tl.location.y
                and br.square.x > tl.square.x and br.square.y > tl.square.x
            ) if (
                self.cell(Point(tl.location.x, br.location.y)).value is None
                and self.cell(Point(br.location.x, tl.location.y)).value is None
            )
        ]

        for rect in rectangles:
            row_cells = [c for c in self.row(rect.top_left.location.y) if c.value is None and c not in rect]
            row_cells.extend([c for c in self.row(rect.bottom_right.location.y) if c.value is None and c not in rect])
            col_cells = [c for c in self.column(rect.top_left.location.x) if c.value is None and c not in rect]
            col_cells.extend([c for c in self.column(rect.bottom_right.location.x) if c.value is None and c not in rect])
            for relation in ["row", "column"]:
                candidates = ALL_CANDIDATES.intersection(*[c.candidates for c in rect])
                candidates -= set().union(*[c.candidates for c in (row_cells if relation == "row" else col_cells)])
                changed = self.remove_candidates_from_cells(
                    (col_cells if relation == "row" else row_cells), candidates
                ) or changed

        return changed

    def solve_wings(self):
        """
        Finds XY, XYZ (not yet implemented) wings

        http://hodoku.sourceforge.net/en/tech_wings.php

        :return: True if changes where made to any cell
        :rtype: bool
        """

        changed = False
        for pivot_cell in [c for c in self.cells if c.value is None and len(c.candidates) == 2]:
            related_cells = self.related_cells(
                pivot_cell,
                filter=lambda c: c.value is None and len(c.candidates) == 2 and c.candidates != pivot_cell.candidates)
            wings = [wc for wc in it.combinations(related_cells, 2)
                     if wc[0].candidates != wc[1].candidates
                     and not wc[0].is_related(wc[1])
                     and len(pivot_cell.candidates | wc[0].candidates | wc[1].candidates) == 3]
            for wing in wings:
                wing_x = wing[0]
                wing_y = wing[1]
                cells = set(iter(self.related_cells(wing_x))) & (set(iter(self.related_cells(wing_y)))) - {pivot_cell}
                changed = Sudoku.remove_candidates_from_cells(
                    cells, wing_x.candidates.intersection(wing_y.candidates)) or changed

        return changed

    def __str__(self):
        """
        The string representation of the board with row and column labels

        :return: Pretty board output
        :rtype: string
        """

        # since strings are immutable, this is my attempt at emulating StringBuffer in Java
        column_labels = list()
        column_labels.append("   ")
        for x in range(0, self.length):
            if x % self.size.height == 0: column_labels.append("  ")
            column_labels.append("{} ".format(chr(ord("A") + x)))
        column_labels.append("    \n")

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
        """
        Merely a convenience method to write the string representation to the standard output

        :return:
        """
        print(str(self))

    def calculate_seed(self):
        """
        Returns a string representation of the cells with values.

        :return: The seed
        :rtype: string
        """

        return "".join("." if c.value is None else str(c) for c in self.cells)


class Cell(object):
    def __init__(self, square, location, value=None):
        """
        Initializes the cell object

        :param square: The square the cell is located in
        :type square: Point
        :param location: The cells location in the board
        :type square: Point
        :param value: The initial value of the cell. If a string is passed it's converted to it's int value based
        on CELL_VALUE_MAP
        :type value: int/char
        """

        self.square = square
        self.location = location
        self.candidates = None
        self.value = value

    def __str__(self):
        """
        The string representation of the cell's value, blank space if no value

        :return: The cell's value
        :rtype: string
        """

        return " " if self.value is None else CELL_VALUE_MAP[self.value]

    def __repr__(self):
        """
        The internal representation of the cell

        :return: Internal representation
        :rtype: string
        """

        return "Cell({}, {}, {})".format(self.square, self.location, self.value)

    def var_to_string(self, var, options=None):
        """
        Method returns a formatted string of the cell's variable


        :param var: square, location, candidates, or value
        :type var: reference
        :param options: formatting options for the variable
        :type options: string
        :return: The formatted string
        :rtype: string
        """

        if var is self.square:
            return "[{sq.x}, {sq.y}]".format(sq=var)
        elif var is self.location:
            if options == "r1c1":
                return "r{}c{}".format(self.location.y + 1, self.location.x + 1)
            elif options == "R1C1":
                return "R{}C{}".format(self.location.y + 1, self.location.x + 1)
            else:
                return "{}{}".format(chr(ord("A") + self.location.x), self.location.y + 1)
        elif var is self.candidates:
            return ", ".join(str(v) for v in self.candidates)
        elif var is self.value:
            return str(var)

    def is_related(self, other_cell):
        """
        Test to see if the other cell is in the same row, column, or square
        :param other_cell: The cell to test
        :type other_cell: Cell
        :return: True if related, false otherwise
        :rtype: bool
        """

        cells = [self, other_cell]
        return Sudoku.is_same_square(cells) or Sudoku.is_same_column(cells) or Sudoku.is_same_row(cells)

    @property
    def value(self):
        """
        Cell value wrapper

        :return: value
        :rtype: int
        """

        return self._value

    @value.setter
    def value(self, value):
        """
        Setter method for value. Allows for int, string input. Strings are converted to int based on the CELL_VALUE_MAP

        :param value: value to set
        :type value: int/string
        :return:
        """
        if isinstance(value, int):
            self._value = value
        elif isinstance(value, str) and len(value) == 1:
            if ord("A") <= ord(value.upper()) <= ord("Z"):
                self._value = ord(value.upper()) - ord("A") + 10
            elif ord("1") <= ord(value) <= ord("9"):
                self._value = int(value)
            else:
                self._value = None
        else:
            self._value = None
        self.candidates = {} if self.value is None else {self.value}


samples = list()
seed = (
    "000005790"
    "000800006"
    "005609403"
    "400003900"
    "090000210"
    "080094300"
    "050001070"
    "308002140"
    "020900605")  # from app
samples.append(Sudoku(seed))

seed = "070004000869000000000000010000010007080009600002057040958003000000001200300000789"  # from app
samples.append(Sudoku(seed))

seed = "090600800000503400807000610000050007000790100000006300070000020040000000203061004"  # from app
samples.append(Sudoku(seed))

seed = "000000000200601005004203900031000850600705009085000470006509200400106007000000000"  # 4831 x-wing
samples.append(Sudoku(seed))

seed = "000000000000000805000071000000000007005090081007008593008023070039005000071060004"  # 3096 xy-wing
samples.append(Sudoku(seed, None))

seed = ("D.8.GC.9..A.E7..659C.7BF.4...3.AG....34.B8.7D..F.B.E1D..9...42.."
        "..1D.....6..953C89EF..7.D.3A.....45.D.A68.1..E.G7...2.F34...8..D"
        "5..B6G1DC794...E.G28E.C.F3B..4D.4...F.....E.5.G..3D..2.86AG.BFC."
        "B7.....1.2D..G862.C.3..B..891D.....6..D...5BF9.2.DG.A..21.4..B73")  # 16x16
samples.append(Sudoku(seed, None))

seed = (".7.81..61...28.5"
        "...7.....6...3.2"
        "..45.....3....41"
        "...1.6...256.7.4")
samples.append(Sudoku(seed, Dimension(2, 4)))

for sample in samples:
    sample.solve()
