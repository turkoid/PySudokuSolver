import re
import numpy as np


class SudokuBoard(object):
    board = None
    width = 3
    height = 3

    def __init__(self, width=3, height=3, initial=None):
        initial = re.sub("\n| ", "", initial)
        self.board = np.array(list(map((lambda x: Cell(x)), list(initial)))).reshape(height * 3, width * 3)

    def row(self, y):
        return self.board[y]

    def column(self, x):
        return self.board[:, x]

    def square(self, x, y, flat=False):
        x *= 3
        y *= 3
        sq = self.board[y:y + 3, x:x + 3]
        if flat:
            sq = sq.reshape(9)
        return sq

    def __str__(self):
        s = ""
        for y in range(0, self.height * 3):
            if y % 3 == 0:
                s += ("-" * (self.width * 8 + 1)) + "\n"
            for x in range(0, self.width * 3):
                if x % 3 == 0:
                    s += "| "
                s += self.board[y, x].display(False) + " "
            s += "|\n"
        s += ("-" * (self.width * 8 + 1)) + "\n"
        return s


class Cell(object):
    pencil_marks = None
    value = 0

    def __init__(self, value=None):
        self.pencil_marks = np.zeros(9, dtype=int)
        if value is not None and int(value) > 0:
            self.value = int(value)
            self.pencil_marks[self.value - 1] = self.value

    def display(self, zero=True):
        return " " if not zero and self.value == 0 else str(self.value)

    def __repr__(self):
        return self.display()


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
print(board.row(1))
print(board.column(7))
print(board.square(0, 1, True))
print(board)
