def char_freq(s):
    d = {}
    for c in s:
        d[c] = d.get(c, 0) + 1
    return d

freq = char_freq('banana')
for k, v in sorted(freq.items()):
    print('%s=%d' % (k, v))
