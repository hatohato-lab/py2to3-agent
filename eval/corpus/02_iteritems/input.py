# クリーンルーム純粋関数（Python 2 記法）: 文字の出現回数。
# dict.iteritems() と print 文は Python 3 では使えない。
def char_freq(s):
    d = {}
    for c in s:
        d[c] = d.get(c, 0) + 1
    return d

freq = char_freq('banana')
for k, v in sorted(freq.iteritems()):
    print '%s=%d' % (k, v)
