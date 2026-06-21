# クリーンルーム純粋関数（Python 2 記法）: 0..n-1 の二乗のリスト。
# Python 3 では print 文・xrange がそのままでは動かない。
def squares(n):
    result = []
    for i in xrange(n):
        result.append(i * i)
    return result

print squares(6)
