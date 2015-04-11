
def nhash(S):
    H = 0
    m = 1
    for c in S[::-1]:
        H = (H + ord(c) * m) & 0xFFFF
        m *= 3
    return H

import sys
print "%x" % (nhash(sys.argv[1]),)
