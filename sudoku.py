import re
import numpy as np
from collections import namedtuple
import itertools as it


Point = namedtuple("Point", "x y")
DEFAULT_BOARD_WIDTH, DEFAULT_BOARD_HEIGHT = 3, 3


def grouper(n, iterable, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return it.zip_longest(fillvalue=fillvalue, *args)


class SudokuBoard(object):
    board = None
    width = DEFAULT_BOARD_WIDTH
    height = DEFAULT_BOARD_HEIGHT
    columns = []
    rows = []
    squares = []

    def __init__(self, data, width=DEFAULT_BOARD_WIDTH, height=DEFAULT_BOARD_HEIGHT):
        self.width = width
        self.height = height

        if data is None:
            data = "0" * (width * height * 9)
            data = re.sub("\n| ", "", data)
        self.board = np.array([Cell(self.index_to_coord(i), v)
                               for i, v in enumerate(list(data))]).reshape(height * 3, width * 3)

        self.rows = [self.row(y).tolist() for y in range(0, self.height * 3)]
        self.columns = [self.column(x).tolist() for x in range(0, self.width * 3)]
        self.squares = [self.square(Point(x, y)).tolist() for y in range(0, self.height) for x in range(0, self.width)]

        self.populate_marks()

    def cell(self, coord):
        return self.board[coord.y][coord.x]

    def row(self, y):
        return self.board[y]

    def column(self, x):
        return self.board[:, x].reshape(self.height * 3)

    def square(self, coord, flat=True):
        x = coord.x * 3
        y = coord.y * 3
        sq = self.board[y:y + 3, x:x + 3]
        if flat:
            sq = sq.reshape(9)
        return sq

    def __str__(self):
        sb = ""
        for y in range(0, self.height * 3):
            if y % 3 == 0:
                sb += ("-" * (self.width * 8 + 1)) + "\n"
            for x in range(0, self.width * 3):
                if x % 3 == 0:
                    sb += "| "
                sb += self.board[y, x].display(False) + " "
            sb += "|\n"
        sb += ("-" * (self.width * 8 + 1)) + "\n"
        return sb

    def index_to_coord(self, index):
        return Point(index % (self.width * 3), int(index / (self.height * 3)))

    def coord_to_index(self, coord):
        return coord.y * (self.height * 3) + coord.x

    def populate_marks(self):
        for row in self.board:
            for cell in row:
                if not cell.is_initial:
                    cell.reset()
                    for mark in range(1, 10):
                        add_mark = True
                        for test_cell in self.get_linked_cells(cell):
                            if test_cell is not cell and test_cell.value == mark:
                                add_mark = False
                                break
                        if add_mark:
                            # oh hai mark
                            cell.add_pencil_marks([mark])

    def solve(self):
        # first set the value for any cell that has only one valid option
        changed = True
        while changed:
            changed = False
            # sole candidate
            changed = changed or self.check_sole_candidates()
            # unique candidate
            changed = changed or self.check_unique_candidates()
            # subsets
            changed = changed or self.check_subsets()
            # blocking subsets
            changed = changed or self.check_blocking_subsets()

    @staticmethod
    def filter_cells(cells, filter, func=""):
        changed = False
        for linked_cell in cells:
            if linked_cell.remove_pencil_marks(filter):
                changed = True
                print("%s: %s - %s" % (func, SudokuBoard.print_coord(linked_cell.coordinate), filter))
        return changed

    def get_linked_cells(self, cell, relations=["square", "row", "column"], include_solved=True, excluded_cells=[]):
        linked_cells = []
        if "square" in relations:
            linked_cells += [c for c in self.square(cell.square)
                             if c is not cell and c not in excluded_cells and (include_solved or c.value == 0)]
        if "row" in relations:
            linked_cells += [c for c in self.row(cell.coordinate.y)
                             if c is not cell and c not in excluded_cells and (include_solved or c.value == 0)
                             and ("square" not in relations or c.square != cell.square)]
        if "column" in relations:
            linked_cells += [c for c in self.column(cell.coordinate.x)
                             if c is not cell and c not in excluded_cells and (include_solved or c.value == 0)
                             and ("square" not in relations or c.square != cell.square)]
        return linked_cells

    def check_sole_candidates(self):
        changed = False
        cells = [cell for row in self.board for cell in row if cell.value == 0]
        for cell in cells:
            values = [mark for mark in cell.pencil_marks if mark != 0]
            if len(values) == 1:
                changed = True
                cell.set_value(values[0])
                SudokuBoard.filter_cells(self.get_linked_cells(cell, include_solved=False), [cell.value], "sole_candidates")
        return changed

    def check_unique_candidates(self):
        changed = False
        cells = [cell for row in self.board for cell in row if cell.value == 0]
        for cell in cells:
            is_cell_changed = False
            for relation in ["square", "row", "column"]:
                linked_cells = self.get_linked_cells(cell, [relation], include_solved=False)
                marks = [mark for mark in cell.pencil_marks if mark != 0]
                for mark in marks:
                    is_unique = True
                    for linked_cell in linked_cells:
                        if linked_cell.pencil_marks[mark - 1] == mark:
                            is_unique = False
                            break
                    if is_unique and len(linked_cells) > 0:
                        cell.set_value(mark)
                        is_cell_changed = True
                        SudokuBoard.filter_cells(self.get_linked_cells(cell, include_solved=False), [cell.value], "unique_candidates")
                        break
                if is_cell_changed:
                    break
            changed = changed or is_cell_changed
        return changed

    def check_subsets(self):
        changed = False
        for relation in ["square", "row", "column"]:
            if relation == "square":
                cell_groups = self.squares
            elif relation == "row":
                cell_groups = self.rows
            elif relation == "column":
                cell_groups = self.columns

            for cell_group in cell_groups:
                cells = [cell for cell in cell_group if cell.value == 0]
                for combo_length in range(2, len(cells) - 1):
                    combinations = it.combinations(cells, combo_length)
                    for combo in combinations:
                        unique_marks = set().union(*[combo_cell.pencil_marks for combo_cell in combo if combo_cell.value == 0]) - {0}
                        if len(unique_marks) == combo_length:
                            changed = SudokuBoard.filter_cells(self.get_linked_cells(combo[0], [relation], False, list(combo)), list(unique_marks), "subsets") or changed
        return changed

    def check_blocking_subsets(self):
        changed = False
        for relation in ["row", "column"]:
            if relation == "row":
                cell_groups = [cell_group for row in self.rows for cell_group in grouper(3, row)]
            elif relation == "column":
                cell_groups = [cell_group for column in self.columns for cell_group in grouper(3, column)]

            for cell_group in cell_groups:
                for link_relation in [relation, "square"]:
                    linked_cells = self.get_linked_cells(cell_group[0], [link_relation], False, list(cell_group))
                    cell_group_marks = set().union(*[cell.pencil_marks for cell in cell_group if cell.value == 0]) - {0}
                    linked_group_marks = set().union(*[cell.pencil_marks for cell in linked_cells if cell.value == 0]) - {0}
                    blocking_marks = cell_group_marks - linked_group_marks
                    if len(blocking_marks) > 0:
                        filter_cells = self.get_linked_cells(cell_group[0], [relation, "square"], False, list(cell_group))
                        changed = SudokuBoard.filter_cells(filter_cells, list(blocking_marks), "blocking_subsets") or changed
        return changed

    @staticmethod
    def print_cells_coordinates(cells):
        return [SudokuBoard.print_coord(c.coordinate) for c in cells]

    @staticmethod
    def print_coord(coord, format_options="1A:{1}{0}"):
        translation_maps = {
            "0": list(range(0, 9)),
            "1": list(range(1, 10)),
            "A": [chr(c) for c in range(ord("A"), ord("A") + 9)]
        }
        index_keys = list(range(0, 9))
        translations = {
            "x": dict(list(zip(index_keys, translation_maps[format_options[0]]))),
            "y": dict(list(zip(index_keys, translation_maps[format_options[1]])))
        }
        return format_options[3:].format(translations["x"][coord.x], translations["y"][coord.y])


class Cell(object):
    pencil_marks = []
    value = 0
    coordinate = None
    square = None
    is_initial = False

    def __init__(self, coordinate, value=None):
        self.coordinate = coordinate
        self.square = Point(int(coordinate.x / 3), int(coordinate.y / 3))
        self.reset()
        self.is_initial = self.set_value(value)

    def display(self, zero=True):
        return " " if not zero and self.value == 0 else str(self.value)

    def __repr__(self):
        return self.display()

    def set_value(self, value):
        if self.coordinate == Point(2, 1) and value == 4:
            print("??")
        if value is not None and int(value) > 0:
            self.value = int(value)
            self.reset()
            self.add_pencil_marks([self.value])
            return True
        return False

    def reset(self):
        self.pencil_marks = [0] * 9

    def add_pencil_marks(self, marks):
        changed = False
        for mark in marks:
            changed = changed or self.pencil_marks[mark - 1] == 0
            self.pencil_marks[mark - 1] = mark
        return changed

    def remove_pencil_marks(self, marks):
        changed = False
        for mark in marks:
            if mark > 0:
                if self.pencil_marks[mark - 1] != 0:
                    changed = True
                    self.pencil_marks[mark - 1] = 0
                changed = changed or self.pencil_marks[mark - 1] != 0
                self.pencil_marks[mark - 1] = 0
        return changed


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
#initial = "070004000869000000000000010000010007080009600002057040958003000000001200300000789"
board = SudokuBoard(initial)
print(board)
board.solve()
print(board)
