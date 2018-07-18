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

    def __init__(self, width=DEFAULT_BOARD_WIDTH, height=DEFAULT_BOARD_HEIGHT, initial=None):
        self.width = width
        self.height = height

        if initial is None:
            initial = "0" * (width * height * 9)
        initial = re.sub("\n| ", "", initial)
        self.board = np.array([Cell(self.index_to_coord(i), v) for i, v in enumerate(list(initial))]).reshape(height * 3, width * 3)

        self.rows = [self.row(y) for y in range(0, height * 3)]
        self.columns = [self.column(x) for x in range(0, width * 3)]
        self.squares = [self.square(Point(x, y), True) for y in range(0, height) for x in range(0, width)]

    def row(self, y):
        return self.board[y]

    def column(self, x):
        return self.board[:, x].reshape(self.height * 3)

    def square(self, coord, flat=False):
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


class Cell(object):
    pencil_marks = None
    value = 0
    coordinate = None

    def __init__(self, coord, value=None):
        self.pencil_marks = np.zeros(9, dtype=int)
        if value is not None and int(value) > 0:
            self.value = int(value)
            self.pencil_marks[self.value - 1] = self.value

    def display(self, zero=True):
        return " " if not zero and self.value == 0 else str(self.value)

    def __repr__(self):
        return self.display()

    def set_value(self, value):
        if value is not None and int(value) > 0:
            self.value = int(value)
            self.pencil_marks = np.zeros(9, dtype=int)
            self.pencil_marks[self.value - 1] = self.value

    def solve(self):
        pass


s = (
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
board = SudokuBoard(initial=s)
# print(board.row(1))
# print(board.column(7))
# print(board.square(0, 1, True))
print(board)
print(board.squares)
