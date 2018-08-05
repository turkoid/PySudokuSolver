from sudoku.constants import *
from sudoku.enums import *
from sudoku.tuples import *
import numpy as np
import itertools as it
import math
from collections import Counter
import re


class Sudoku(object):
    def __init__(self, seed, size=DEFAULT_BOX_SIZE):
        """
        Initializes the sudoku board

        :param seed: The starting values for the board. Use the alpha equivalent for double digit numbers
        :type seed: Iterable
        :param size: Dimension of the box, not the board. Defaults to 3x3
        :type size: Dimension
        """

        self.seed = [str(v) for v in list(seed)]
        if size is None:
            # Try to determine the size of box by taking the 4th root of the seed length
            size = int(math.sqrt(math.sqrt(len(self.seed))))
            self.size = Dimension(size, size)
        else:
            self.size = size
        self.length = self.size.width * self.size.height
        self.ALL_CANDIDATES = set(range(1, self.length + 1))

        # Create each cell based on the seed value
        self.cells = [
            Cell(self.cell_box(loc), loc, v)
            for loc, v in (
                (self.index_to_location(i), v)
                for i, v in it.zip_longest(range(0, self.length**2), self.seed, fillvalue=None)
            )
        ]
        self.board = np.array(self.cells).reshape(self.length, self.length)

        self.rows = [self.row(y) for y in range(0, self.length)]
        self.columns = [self.column(x) for x in range(0, self.length)]
        self.boxes = [self.box(Point(x, y))
                      for y in range(0, self.size.height)
                      for x in range(0, self.size.width)]

        self.populate_candidates()
        self.solve_steps = []

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

    def cell_box(self, location):
        """
        The box the cell is in

        :param location: The x,y location of the cell
        :type location: Point
        :return: The x,y location of the box containing the cell
        :rtype: Point
        """

        return Point(int(location.x / self.size.height), int(location.y / self.size.width))

    def cell(self, location):
        """
        Returns the cell at location

        :param location: The x, y location within all the cells
        :type location: Union[Point, str]
        :return: The Cell
        :rtype: Cell
        """

        if isinstance(location, str):
            location_match = re.match("([A-Z])(\d+)", location.upper())
            if location_match:
                return self.board[int(location_match.group(2)) - 1][ord(location_match.group(1)) - ord("A")]
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
        return (cells.flatten() if flatten else cells).tolist()

    def row(self, y):
        """
        The group of cells at row y
        :param y: The row index
        :type y: int
        :return: Row cells
        :rtype: list
        """

        return self.board[y].tolist()

    def box(self, location, flatten=True):
        """
        The group of cells at box location

        :param location: The x,y location of the box
        :type location: Point
        :param flatten: Flattens the MxN array into a (M*N)x1 array
        :type flatten: bool
        :return: box cells
        :rtype: list
        """

        cells = self.board[
                location.y * self.size.width:(location.y + 1) * self.size.width,
                location.x * self.size.height:(location.x + 1) * self.size.height]
        return (cells.flatten() if flatten else cells).tolist()

    def related_cells(self, parent, relations=None, cell_filter=None):
        """
        The group of cells that share a relation to the parent cell

        :param parent: The cell to find its relatives
        :type parent: Cell
        :param relations: The relationships to search for. If nothing is passed, it defaults to all
        :type relations: set
        :param cell_filter: Function used to filter out unwanted cells
        :type cell_filter: Function
        :return: Related cells
        :rtype: list
        """

        if relations is None: relations = CellRelation.all()

        cells = {}
        if CellRelation.BOX in relations:
            cells |= set(self.box(parent.box))
        if CellRelation.ROW in relations:
            cells |= set(self.row(parent.location.y))
        if CellRelation.COLUMN in relations:
            cells |= set(self.column(parent.location.x))
        cells -= {parent}
        return list(cells) if cell_filter is None else [c for c in cells if cell_filter(c)]

    @staticmethod
    def is_same_column(cells):
        """
        Test to see if all cells are in the same column

        :param cells: Cells to test
        :type cells: Iterable
        :return: True if same column, false otherwise
        :rtype: bool
        """

        return not cells or [c.location.x for c in cells].count(cells[0].location.x) == len(cells)

    @staticmethod
    def is_same_row(cells):
        """
        Test to see if all cells are in the same row

        :param cells: Cells to test
        :type cells: Iterable
        :return: True if same row, false otherwise
        :rtype: bool
        """

        return not cells or [c.location.y for c in cells].count(cells[0].location.y) == len(cells)

    @staticmethod
    def is_same_box(cells):
        """
        Test to see if all cells are in the same box

        :param cells: Cells to test
        :type cells: Iterable
        :return: True if same box, false otherwise
        :rtype: bool
        """

        return not cells or [c.box for c in cells].count(cells[0].box) == len(cells)

    @staticmethod
    def remove_candidates_from_cells(cells, candidates):
        if not candidates: return False
        cells = [c for c in cells if c.value is None and not c.candidates.isdisjoint(candidates)]
        for cell in cells: cell.candidates -= candidates
        return len(cells) > 0

    def populate_candidates(self):
        """
        Populates all cells with no value with possible candidates

        :return:
        """

        for cell in [c for c in self.cells if c.value is None]:
            cell.candidates = self.ALL_CANDIDATES.difference(
                (rc.value for rc in self.related_cells(cell, cell_filter=lambda c: c.value is not None)))
            if cell.var_changed("candidates"):
                self.solve_steps.append(Step(TechniqueArchetype))

    def apply_technique(self, technique, cells, values, info=None):
        """
        Applies the technique given to the given cells

        :param technique: The technique to use
        :type technique: Technique
        :param cells: The cells
        :type cells: iterable
        :param values: The values to use
        :type values: iterable
        :param info: Extra information to help format the log entry
        :type info: str
        :return: True if a cell's value changed or any cell candidates
        :rtype: bool
        """

        if not cells or not values: return False

        if technique.type in {TechniqueArchetype.NAKED, TechniqueArchetype.HIDDEN} and technique.size == 1:
            cells[0].value = next(iter(values))

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

        :return: True if changes where made to any cell, otherwise False
        :rtype: bool
        """

        changed = False
        cells = [c for c in self.cells if c.value is None]
        for cell in cells:
            if len(cell.candidates) == 1:
                candidates = cell.candidates
            else:
                for relation in CellRelation.all():
                    candidates = cell.candidates.difference(
                        *[rc.candidates
                          for rc in self.related_cells(cell, {relation}, cell_filter=lambda c: c.value is None)]
                    )
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
        or box, then the related cells cannot contain the subsets' candidates

        :return: True if changes where made to any cell
        :rtype: bool
        """

        changed = False
        for relation in CellRelation.all():
            # this is filtering the multi-dimensional array of rows, columns, or boxes so that each sub-array contains
            # only cells with no value set
            cell_groups = [grp for grp in [[c for c in grp if c.value is None] for grp in (
                self.boxes if relation == CellRelation.BOX
                else self.rows if relation == CellRelation.ROW
                else self.columns
            )] if grp]
            for cells in cell_groups:
                # we only check for subsets of at least size 2 and 1 less then the total number cells
                for subset_length in range(2, len(cells) - 1):
                    for subset in it.combinations(cells, subset_length):
                        other_cells = [c for c in cells if c not in subset]
                        candidates = set().union(*[c.candidates for c in subset])
                        candidates -= set().union(*[c.candidates for c in other_cells])
                        if len(candidates) == subset_length:
                            changed = Sudoku.remove_candidates_from_cells(
                                subset, candidates.symmetric_difference(
                                    set().union(*[c.candidates for c in subset])
                                )) or changed
                            changed = Sudoku.remove_candidates_from_cells(other_cells, candidates) or changed
                            blocking_relation = None
                            if relation == CellRelation.BOX:
                                if Sudoku.is_same_column(subset):
                                    blocking_relation = CellRelation.COLUMN
                                elif Sudoku.is_same_row(subset):
                                    blocking_relation = CellRelation.ROW
                            elif Sudoku.is_same_box(subset):
                                blocking_relation = CellRelation.BOX
                            if blocking_relation is not None:
                                changed = Sudoku.remove_candidates_from_cells(self.related_cells(
                                    subset[0], {blocking_relation}, cell_filter=lambda c: c.value is None and c not in subset
                                ), candidates) or changed
        return changed

    def solve_fish(self):
        """
        Uses the fish solving technique

        http://hodoku.sourceforge.net/en/tech_fishb.php

        X-Wing - an x-wing is a special type of 2x2 fish
        Swordfish - 3x3 fish
        Jellyfish - 4x4 fish

        :return: True if changes where made to any cell, otherwise False
        :rtype: bool
        """

        changed = False

        for relation in {CellRelation.ROW, CellRelation.COLUMN}:
            # filter out cells with values
            cell_grouping = [
                [c for c in grp if c.value is None]
                for grp in (self.rows if relation == CellRelation.ROW else self.columns)
            ]
            # finds naked or hidden subsetS
            group_sets = [grp for grp in [
                [
                    subset
                    for subset_length in range(2, len(grp) + 1)
                    for subset in it.combinations(grp, subset_length)
                    if len(self.ALL_CANDIDATES.intersection(*[c.candidates for c in subset]) -
                           set().union(*[c.candidates for c in grp if c not in subset])) >= 1
                ]
                for grp in cell_grouping
            ] if grp]
            if len(group_sets) < 2: return False
            # this will find all combinations of subsets from each row/column
            # then it only allows where they have at least one common candidate
            # and also that there is at least 2 intersections of each cell
            fishes = [
                [c for subset in fish for c in subset]
                for fish_size in range(2, 3)
                for fish_stock in it.combinations(group_sets, fish_size)
                for fish in it.product(*fish_stock)
                if len(self.ALL_CANDIDATES.intersection(*[c.candidates for subset in fish for c in subset])) >= 1
                and len(
                    [cnt for _, cnt in
                     Counter([
                         c.location.x if relation == CellRelation.ROW else c.location.y
                         for subset in fish
                         for c in subset]
                     ).items() if cnt == 1]
                ) == 0
            ]
            # lets do the magic
            for fish in fishes:
                base_indices = {c.location.x if relation == CellRelation.COLUMN else c.location.y for c in fish}
                cover_indices = {c.location.y if relation == CellRelation.COLUMN else c.location.x for c in fish}
                candidates = self.ALL_CANDIDATES.intersection(*[c.candidates for c in fish])
                candidates -= set().union(*[
                    c.candidates
                    for index in base_indices
                    for c in (self.column(index) if relation == CellRelation.COLUMN else self.row(index))
                    if c.value is None and c not in fish
                ])
                cells = [
                    c
                    for index in cover_indices
                    for c in (self.row(index) if relation == CellRelation.COLUMN else self.column(index))
                    if c.value is None and c not in fish
                ]
                changed = self.remove_candidates_from_cells(cells, candidates) or changed

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
                cell_filter=lambda c:
                c.value is None and len(c.candidates) == 2 and c.candidates != pivot_cell.candidates
            )
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
        :rtype: str
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
        :rtype: str
        """

        return "".join("." if c.value is None else str(c) for c in self.cells)


class Cell(object):
    def __init__(self, box, location, value=None):
        """
        Initializes the cell object

        :param box: The box the cell is located in
        :type box: Point
        :param location: The cells location in the board
        :type box: Point
        :param value: The initial value of the cell. If a string is passed it's converted to it's int value based
        on CELL_VALUE_MAP
        :type value: Union[int,
        """

        self.box = box
        self.location = location
        self.candidates = {}
        self.value = value

    def __str__(self):
        """
        The string representation of the cell's value, blank space if no value

        :return: The cell's value
        :rtype: str
        """

        return " " if self.value is None else CELL_VALUE_MAP[self.value]

    def __repr__(self):
        """
        The internal representation of the cell

        :return: Internal representation
        :rtype: string
        """

        return "Cell({}, {}, {})".format(self.box, self.location, self.value)

    def var_to_string(self, var, options=None):
        """
        Method returns a formatted string of the cell's variable

        :param var: box, location, candidates, or value
        :type var: str
        :param options: formatting options for the variable
        :type options: str
        :return: The formatted string
        :rtype: str
        """

        if var == "box":
            return "[{sq.x}, {sq.y}]".format(sq=self.box)
        elif var == "location":
            if options == "r1c1":
                return "r{}c{}".format(self.location.y + 1, self.location.x + 1)
            elif options == "R1C1":
                return "R{}C{}".format(self.location.y + 1, self.location.x + 1)
            else:
                return "{}{}".format(chr(ord("A") + self.location.x), self.location.y + 1)
        elif var == "candidates":
            return "{{{}}}".format(", ".join(CELL_VALUE_MAP[v] for v in self.candidates))
        elif var == "value":
            return str(var) if self.value is not None or options is None else options

    def is_related(self, other_cell):
        """
        Test to see if the other cell is in the same row, column, or box
        :param other_cell: The cell to test
        :type other_cell: Cell
        :return: True if related, false otherwise
        :rtype: bool
        """

        cells = [self, other_cell]
        return Sudoku.is_same_box(cells) or Sudoku.is_same_column(cells) or Sudoku.is_same_row(cells)

    @property
    def value(self):
        """
        Cell variable wrapper

        :return: value
        :rtype: int
        """

        return self._value

    @value.setter
    def value(self, value):
        """
        Setter method for value. Allows for int, string input. Strings are converted to int based on the CELL_VALUE_MAP
        Stores the previous value to track changes

        :param value: value to set
        :type value: Union[int, str]
        :return:
        """

        self._prev_value = self._value
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

    @property
    def candidates(self):
        """
        Candidates variables wrapper

        :return: set
        """

        return self._candidates

    @candidates.setter
    def candidates(self, value):
        """
        Candidate setter wrapper
        Stores the previous value to track changes

        :param value: The candidates
        :type value: set
        :return:
        """

        self._prev_candidates = {} if self._candidates is None else self._candidates
        self._candidates = {} if value is None else value

    def var_changed(self, var):
        """
        Tests whether the given var has changed.
        Only works for "value" and "candidates"

        :param var: Variable to test
        :type var: str
        :return: True if changed, False otherwise and the changed var
        :rtype: bool, Union[int, set]
        """

        if var == "value":
            return self.value != self._prev_value, self._prev_value
        elif var == "candidates":
            return self.candidates != self._prev_candidates, self._prev_candidates
        else:
            return False, None


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

# x-wing test
samples = list()
seed = (".41729.3."
        "769..34.2"
        ".3264.719"
        "4.39..17."
        "6.7..49.3"
        "19537..24"
        "214567398"
        "376.9.541"
        "958431267")
samples.append(Sudoku(seed))

# 8396 9565
for sample in samples:
    sample.solve()
