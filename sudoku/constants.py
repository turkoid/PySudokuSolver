from sudoku.tuples import Dimension


# the default dimension of a single box (not the board)
DEFAULT_BOX_SIZE = Dimension(3, 3)
# The max is 25 only because of column labeling (A-Z). If i didn't output to only console, this limit could be increased
MAX_CELL_VALUE = 25
# Dictionary from cell value to single character (after 9, alpha characters are used)
CELL_VALUE_MAP = dict(list(zip(
    range(0, MAX_CELL_VALUE + 1),
    [" "] + [str(i) for i in range(1, 10)] + [chr(code) for code in range(ord("A"), ord("A") + MAX_CELL_VALUE - 9)]
)))