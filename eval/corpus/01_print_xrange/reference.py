# 正例（陽性対照）: input.py を Python 3 へ正しく移植したもの。
# オラクルはこれを PASS と判定できなければならない（自己検証）。
def squares(n):
    result = []
    for i in range(n):
        result.append(i * i)
    return result

print(squares(6))
