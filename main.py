from sudoku.puzzle import *


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

seed = "000000000200601005004203900031000850600705009085000470006509200400106007000000000"  # 4831 x-wing 4831-xwing
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

samples = list()
seed = "000000000200601005004203900031000850600705009085000470006509200400106007000000000"  # 4831 x-wing
samples.append(Sudoku(seed))

# 8396 9565
for sample in samples:
    sample.solve()
    print(sample.solution())
