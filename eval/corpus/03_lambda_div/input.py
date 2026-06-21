# クリーンルーム純粋関数（Python 2 記法）: 各ペアの平均（整数）。
# lambda のタプル引数・map のリスト返し・/ の整数除算は Python 3 で挙動が変わる。
def averages(pairs):
    return map(lambda (a, b): (a + b) / 2, pairs)

print averages([(1, 3), (2, 4), (10, 20)])
