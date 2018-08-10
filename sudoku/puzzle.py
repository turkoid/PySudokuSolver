from __future__ import annotations
from sudoku.dependencies import *
import sudoku.solution as solution
import numpy as np
import itertools as it
import math
from collections import Counter
import re


class Sudoku(object):
    def __init__(self, seed: Iterable, size: Optional[Dimension] = DEFAULT_BOX_SIZE) -> None:
        """
        Initializes the sudoku board

        :param seed: The starting values for the board. Use the alpha equivalent for double digit numbers
        :param size: Dimension of the box, not the board. Defaults to 3x3
        """

        self.seed = [str(v) for v in iter(seed)]
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

        self.solve_steps = []
        self.populate_candidates()

    def reset(self) -> None:
        """
        Resets the board to the seed value

        :return:
        """

        for cell, value in zip(self.cells, self.seed):
            cell.value = value

    def index_to_location(self, index: int) -> Point:
        """
        Converts the index in all the cells to a point

        :param index: Index within all cells
        :return: The x, y location of the cell within the board
        """

        return Point(index % self.length, int(index / self.length))

    def location_to_index(self, location: Point) -> int:
        """
        Converts a point to the index in all the cells

        :param location: The x, y location of the cell within the board
        :return: Index within all cells
        """

        return location.y * self.length + location.x

    def cell_box(self, location: Point) -> Point:
        """
        The box the cell is in

        :param location: The x,y location of the cell
        :return: The x,y location of the box containing the cell
        """

        return Point(int(location.x / self.size.height), int(location.y / self.size.width))

    def cell(self, location: Point) -> Cell:
        """
        Returns the cell at location

        :param location: The x, y location within all the cells
        :return: The Cell
        """

        if isinstance(location, str):
            location_match = re.match("([A-Z])(\d+)", location.upper())
            if location_match:
                return self.board[int(location_match.group(2)) - 1][ord(location_match.group(1)) - ord("A")]
        return self.board[location.y][location.x]

    def column(self, x: int, flatten: bool = True) -> List[Cell]:
        """
        The group of cells at column x

        :param x: The column index
        :param flatten: Flattens the 1xN into a Nx1 array
        :return: Column cells
        """

        cells = self.board[:, x]
        return (cells.flatten() if flatten else cells).tolist()

    def row(self, y: int) -> List[Cell]:
        """
        The group of cells at row y
        :param y: The row index
        :return: Row cells
        """

        return self.board[y].tolist()

    def box(self, location: Point, flatten: bool = True) -> List[Cell]:
        """
        The group of cells at box location

        :param location: The x,y location of the box
        :param flatten: Flattens the MxN array into a (M*N)x1 array
        :return: box cells
        """

        cells = self.board[
                location.y * self.size.width:(location.y + 1) * self.size.width,
                location.x * self.size.height:(location.x + 1) * self.size.height]
        return (cells.flatten() if flatten else cells).tolist()

    def related_cells(self, parent: Cell, relations: Optional[Set[CellRelation]] = None,
                      cell_filter: Optional[Callable] = None) -> List[Cell]:
        """
        The group of cells that share a relation to the parent cell

        :param parent: The cell to find its relatives
        :param relations: The relationships to search for. If nothing is passed, it defaults to all
        :param cell_filter: Function used to filter out unwanted cells
        :return: Related cells
        """

        if relations is None: relations = ALL_RELATIONS

        cells = set()
        if CellRelation.BOX in relations:
            cells |= set(self.box(parent.box))
        if CellRelation.ROW in relations:
            cells |= set(self.row(parent.location.y))
        if CellRelation.COLUMN in relations:
            cells |= set(self.column(parent.location.x))
        cells -= {parent}
        return list(cells) if cell_filter is None else [c for c in cells if cell_filter(c)]

    def populate_candidates(self) -> None:
        """
        Populates all cells with no value with possible candidates

        :return:
        """

        cells = [c for c in self.cells if c.value is None]

        if cells:
            for cell in cells:
                cell.candidates = self.ALL_CANDIDATES.difference(
                    (rc.value for rc in self.related_cells(cell, cell_filter=lambda c: c.value is not None)))
            cells = [c for c in cells if c.candidates != c.old_candidates]
            if cells: self.solve_steps.append(solution.step_populate(cells, self.ALL_CANDIDATES))

    def apply_technique(self, technique: Technique, source_cells: Iterable[Cell], values: Set[int]) -> bool:
        """
        Applies the technique given to the given cells

        :param technique: The technique to use
        :param source_cells: The cells
        :param values: The values to use
        :return: True if a cell's value changed or any cell candidates
        """

        if not source_cells or not values: return False

        actions = []
        cells = list(source_cells)
        if technique.type in [TechniqueArchetype.NAKED, TechniqueArchetype.HIDDEN] and technique.size == 1:
            cells[0].value = next(iter(values))
            if cells[0].value_changed():
                actions.append(solution.action_solve(cells[0]))
        elif technique.type is TechniqueArchetype.HIDDEN:
            modified = modify_cell_candidates(cells, frozenset.intersection, values)
            if modified:
                actions.append(solution.action_intersection(modified, values))

        target_cells = None
        if technique.type is TechniqueArchetype.WING:
            # right now only handle xy-wing
            pivot_cell = cells[0]
            wing_x = cells[1]
            wing_y = cells[2]
            target_cells = set(iter(self.related_cells(wing_x)))
            target_cells &= (set(iter(self.related_cells(wing_y))))
            target_cells -= {pivot_cell}
        else:
            target_cells = set().union(*[self.related_cells(
                c, technique.target_relation,
                cell_filter=lambda c: c.value is None and c not in source_cells)
                for c in source_cells
            ])
        if target_cells:
            modified = modify_cell_candidates(target_cells, frozenset.difference, values)
            if modified:
                actions.append(solution.action_difference(modified, values))

        if actions:
            self.solve_steps.append(solution.Step(technique, source_cells, values, actions))
            return True

        return False

    def solve(self) -> None:
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

    def solve_singles(self) -> bool:
        """
        This technique finds naked singles and hidden singles

        http://hodoku.sourceforge.net/en/tech_singles.php

        Naked single - Cell contains exactly one candidate
        Hidden single - The cell within the related cells can only contain this candidate

        :return: True if changes where made to any cell, otherwise False
        """

        changed = False
        cells = [c for c in self.cells if c.value is None]
        for cell in cells:
            if len(cell.candidates) == 1:
                changed = self.apply_technique(
                    Technique(TechniqueArchetype.NAKED, 1, None, ALL_RELATIONS),
                    [cell],
                    cell.candidates) or changed
            else:
                for relation in ALL_RELATIONS:
                    candidates = cell.candidates.difference(
                        *[rc.candidates
                          for rc in self.related_cells(cell, {relation}, cell_filter=lambda c: c.value is None)]
                    )
                    if len(candidates) == 1:
                        changed = self.apply_technique(
                            Technique(TechniqueArchetype.HIDDEN, 1, {relation}, ALL_RELATIONS),
                            [cell],
                            candidates
                        )

        return changed

    def solve_subsets(self) -> bool:
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
        """

        changed = False
        for relation in ALL_RELATIONS:
            # this is filtering the multi-dimensional array of rows, columns, or boxes so that each sub-array contains
            # only cells with no value set
            cell_groups = [grp for grp in [[c for c in grp if c.value is None] for grp in (
                self.boxes if relation is CellRelation.BOX
                else self.rows if relation is CellRelation.ROW
                else self.columns
            )] if grp]
            for cells in cell_groups:
                # we only check for subsets of at least size 2 and 1 less then the total number cells
                for subset_length in range(2, len(cells) - 1):
                    for subset in it.combinations(cells, subset_length):
                        other_cells = [c for c in cells if c not in subset]
                        source_candidates = set().union(*[c.candidates for c in subset])
                        target_candidates = source_candidates - set().union(*[c.candidates for c in other_cells])
                        if len(target_candidates) == subset_length:
                            changed = self.apply_technique(
                                Technique(TechniqueArchetype.NAKED
                                          if source_candidates == target_candidates else
                                          TechniqueArchetype.HIDDEN,
                                          len(target_candidates), {relation}, {relation}),
                                subset, target_candidates) or changed
                        elif len(target_candidates) < subset_length:
                            target_relation = None
                            if relation is CellRelation.BOX:
                                if is_same_column(subset):
                                    target_relation = CellRelation.COLUMN
                                elif is_same_row(subset):
                                    target_relation = CellRelation.ROW
                            elif is_same_box(subset):
                                target_relation = CellRelation.BOX
                            if target_relation is not None:
                                changed = self.apply_technique(
                                    Technique(TechniqueArchetype.LOCKED, subset_length, {relation}, {target_relation}),
                                    subset, target_candidates) or changed
                                
        return changed

    def solve_fish(self) -> bool:
        """
        Uses the fish solving technique

        http://hodoku.sourceforge.net/en/tech_fishb.php

        X-Wing - an x-wing is a special type of 2x2 fish
        Swordfish - 3x3 fish
        Jellyfish - 4x4 fish

        :return: True if changes where made to any cell, otherwise False
        """

        changed = False

        for relation in {CellRelation.ROW, CellRelation.COLUMN}:
            # filter out cells with values
            cell_grouping = [
                [c for c in grp if c.value is None]
                for grp in (self.rows if relation is CellRelation.ROW else self.columns)
            ]
            # finds naked or hidden subsets
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
                Fish(fish_size, [c for subset in fish for c in subset])
                for fish_size in range(2, len(group_sets) + 1)
                for fish_stock in it.combinations(group_sets, fish_size)
                for fish in it.product(*fish_stock)
                if len({c.location.x if relation is CellRelation.ROW else c.location.y for subset in fish for c in subset}) == fish_size
                and len(self.ALL_CANDIDATES.intersection(*[c.candidates for subset in fish for c in subset])) >= 1
                and len(
                    [cnt for _, cnt in
                     Counter([
                         c.location.x if relation is CellRelation.ROW else c.location.y
                         for subset in fish
                         for c in subset]
                     ).items() if cnt == 1]
                ) == 0
            ]
            # lets do the magic
            for fish in fishes:
                candidates = self.ALL_CANDIDATES.intersection(*[c.candidates for c in fish.cells])
                candidates -= set().union(*[
                    rc.candidates
                    for c in fish.cells
                    for rc in self.related_cells(c, {relation})
                    if rc.value is None and rc not in fish.cells
                ])
                changed = self.apply_technique(
                    Technique(TechniqueArchetype.FISH, 
                              fish.size, 
                              {relation}, 
                              {CellRelation.ROW if relation is CellRelation.COLUMN else CellRelation.COLUMN}),
                    fish.cells,
                    candidates
                ) or changed

        return changed

    def solve_wings(self) -> bool:
        """
        Finds XY, XYZ (not yet implemented) wings

        http://hodoku.sourceforge.net/en/tech_wings.php

        :return: True if changes where made to any cell
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
                changed = self.apply_technique(
                    Technique(TechniqueArchetype.WING, 2, None, ALL_RELATIONS),
                    [pivot_cell, *wing],
                    wing[0].candidates.intersection(wing[1].candidates)
                )

        return changed

    def __str__(self) -> str:
        """
        The string representation of the board with row and column labels

        :return: Pretty board output
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

    def print(self) -> None:
        """
        Merely a convenience method to write the string representation to the standard output

        :return:
        """
        print(str(self))

    def calculate_seed(self) -> str:
        """
        Returns a string representation of the cells with values.

        :return: The seed
        """

        return "".join("." if c.value is None else str(c) for c in self.cells)

    def solution(self) -> str:
        buffer = list()
        for i, step in enumerate(self.solve_steps):
            buffer.append("\nStep {i}: {info}".format(i=i + 1, info=str(step)))
        return "".join(buffer)


class Cell(object):
    def __init__(self, box: Point, location: Point, value: Union[int, str] = None) -> None:
        """
        Initializes the cell object

        :param box: The box the cell is located in
        :param location: The cells location in the board
        :param value: The initial value of the cell. If a string is passed it's converted to it's int value based
        on CELL_VALUE_MAP
        """

        self.box = box
        self.location = location
        self.candidates = NO_CANDIDATES
        self.value = value

    def __str__(self) -> str:
        """
        The string representation of the cell's value, blank space if no value

        :return: The cell's value
        """

        return " " if self.value is None else CELL_VALUE_MAP[self.value]

    def __repr__(self) -> str:
        """
        The internal representation of the cell

        :return: Internal representation
        """

        return "Cell({}, {}, {})".format(self.box, self.location, self.value)

    def var_to_string(self, var: str, options: Optional[str] = None) -> str:
        """
        Method returns a formatted string of the cell's variable

        :param var: box, location, candidates, or value
        :param options: formatting options for the variable
        :return: The formatted string
        """

        if var == "box":
            return "[{sq.x}, {sq.y}]".format(sq=Point(self.box.x + 1, self.box.y + 1))
        elif var == "location":
            if options == "r1c1":
                return "r{}c{}".format(self.location.y + 1, self.location.x + 1)
            elif options == "R1C1":
                return "R{}C{}".format(self.location.y + 1, self.location.x + 1)
            else:
                return "{}{}".format(chr(ord("A") + self.location.y), self.location.x + 1)
                # return "{}{}".format(chr(ord("A") + self.location.x), self.location.y + 1)
        elif var == "candidates":
            return "{{{}}}".format(", ".join(CELL_VALUE_MAP[v] for v in self.candidates))
        elif var == "value":
            return str(var) if self.value is not None or options is None else options

    def is_related(self, other_cell: "Cell") -> bool:
        """
        Test to see if the other cell is in the same row, column, or box
        :param other_cell: The cell to test
        :return: True if related, false otherwise
        """

        cells = [self, other_cell]
        return is_same_box(cells) or is_same_column(cells) or is_same_row(cells)

    @property
    def value(self) -> int:
        """
        Cell variable wrapper

        :return: value
        """

        return self._value

    @value.setter
    def value(self, value: Union[int, str]) -> None:
        """
        Setter method for value. Allows for int, string input. Strings are converted to int based on the CELL_VALUE_MAP
        Stores the previous value to track changes

        :param value: value to set
        :return:
        """

        try:
            self.old_value = NO_CANDIDATES if self._value is None else self._value
        except AttributeError:
            self.old_value = None
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
        self.candidates = {self.value} if self.value else NO_CANDIDATES

    @property
    def candidates(self) -> Set[int]:
        """
        Candidates variables wrapper

        :return: set
        """

        return self._candidates

    @candidates.setter
    def candidates(self, value: Set[int]) -> None:
        """
        Candidate setter wrapper
        Stores the previous value to track changes

        :param value: The candidates
        :return:
        """

        try:
            self.old_candidates = NO_CANDIDATES if self._candidates is None else self._candidates
        except AttributeError:
            self.old_candidates = frozenset(value)
        self._candidates = frozenset(value) if value else NO_CANDIDATES

    def value_changed(self) -> bool:
        return self.old_value != self.value

    def candidates_changed(self) -> bool:
        return self.old_candidates != self.candidates


def is_same_column(cells: Iterable[Cell]) -> bool:
    """
    Test to see if all cells are in the same column

    :param cells: Cells to test
    :return: True if same column, false otherwise
    """

    if cells: cells = list(cells)
    return cells and [c.location.x for c in cells].count(cells[0].location.x) == len(cells)


def is_same_row(cells: Iterable[Cell]) -> bool:
    """
    Test to see if all cells are in the same row

    :param cells: Cells to test
    :return: True if same row, false otherwise
    """

    if cells: cells = list(cells)
    return not cells or [c.location.y for c in cells].count(cells[0].location.y) == len(cells)


def is_same_box(cells: Iterable[Cell]) -> bool:
    """
    Test to see if all cells are in the same box

    :param cells: Cells to test
    :return: True if same box, false otherwise
    """

    if cells: cells = list(cells)
    return not cells or [c.box for c in cells].count(cells[0].box) == len(cells)


def modify_cell_candidates(cells: Iterable[Cell], op: ModifyOperation,
                           candidates: Set[int]) -> List[Cell]:
    if not cells or not candidates: return []
    for cell in cells: cell.candidates = op(cell.candidates, candidates)
    return [c for c in cells if c.candidates_changed()]
