import re
import numpy as np
from collections import namedtuple


Point = namedtuple("Point", "x y")
DEFAULT_BOARD_WIDTH, DEFAULT_BOARD_HEIGHT = 3, 3


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
        self.board = np.array([Cell(self.index_to_coord(i), v) for i, v in enumerate(list(data))]).reshape(height * 3, width * 3)

        self.rows = [self.row(y) for y in range(0, self.height * 3)]
        self.columns = [self.column(x) for x in range(0, self.width * 3)]
        self.squares = [self.square(Point(x, y)) for y in range(0, self.height) for x in range(0, self.width)]

        self.populate_marks()

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
                            if test_cell is not cell and test_cell == mark:
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

    def filter_linked_cells(self, cell, filter):
        for linked_cell in self.get_linked_cells(cell, include_solved=False):
            linked_cell.remove_pencil_marks(filter)

    def get_linked_cells(self, cell, relations=["square", "row", "column"], include_solved=True):
        linked_cells = []
        if "square" in relations:
            linked_cells += [c for c in self.square(cell.square) if c is not cell and (include_solved or c.value != 0)]
        if "row" in relations:
            linked_cells += [c for c in self.column(cell.coordinate.x) if c is not cell and (not "square" in relations or c.square.y != cell.square.y) and (include_solved or c.value != 0)]
        if "column" in relations:
            linked_cells += [c for c in self.row(cell.coordinate.y) if c is not cell and (not "square" in relations or c.square.x != cell.square.x) and (include_solved or c.value != 0)]
        return linked_cells

    def check_sole_candidates(self):
        changed = False
        cells = [cell for row in self.board for cell in row if cell.value == 0]
        for cell in cells:
            values = [mark for mark in cell.pencil_marks if mark != 0]
            if len(values) == 1:
                changed = True
                cell.set_value(values[0])
                self.filter_linked_cells(cell, [cell.value])
        return changed

    def check_unique_candidates(self):
        changed = False
        cells = [cell for row in self.board for cell in row if cell.value == 0]
        for cell in cells:
            is_cell_changed = False
            for relation in ["square", "row", "column"]:
                linked_cells = self.get_linked_cells(cell, [relation], include_solved=True)
                marks = [mark for mark in cell.pencil_marks if mark != 0]
                for mark in marks:
                    is_unique = True
                    for linked_cell in linked_cells:
                        if linked_cell.pencil_marks[mark - 1] == mark:
                            is_unique = False
                            break
                    if is_unique:
                        cell.set_value(mark)
                        is_cell_changed = True
                        self.filter_linked_cells(cell, [cell.value])
                        break
                if is_cell_changed:
                    break
            changed = changed or is_cell_changed
        return changed

    def check_naked_subsets(self):
        pass


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
        if value is not None and int(value) > 0:
            self.value = int(value)
            self.reset()
            self.add_pencil_marks([self.value])
            return True
        return False

    def reset(self):
        self.pencil_marks = [0] * 9

    def __eq__(self, other):
        if isinstance(other, Cell):
            return self.value == other.value
        elif isinstance(other, list):
            return self.pencil_marks == other
        else:
            return self.value == other

    def add_pencil_marks(self, marks):
        for mark in marks:
            self.pencil_marks[mark - 1] = mark

    def remove_pencil_marks(self, marks):
        for mark in marks:
            self.pencil_marks[mark - 1] = 0


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
board = SudokuBoard(initial)
# print(board.row(1))
# print(board.column(7))
# print(board.square(0, 1, True))
print(board)
board.solve()
print(board)