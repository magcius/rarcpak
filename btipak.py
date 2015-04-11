#!/usr/bin/env python

import os
import os.path
import struct
import sys


head = """09 02 00 30 00 30 00 00 01 02 00 A0 00 00 09 20 00 00 00 00 01 01 00 00 01 00 00 00 00 00 00 20""".replace(' ', '').decode('hex')

def rgb5a3(p):
    r,g,b,a = p
    if a == 0xFF:
        n = 0x8000
        r = int((r / 255.0) * 31)
        g = int((g / 255.0) * 31)
        b = int((b / 255.0) * 31)
        return n | (r << 10) | (g << 5) | b
    else:
        a = int((a / 255.0) * 7)
        r = int((r / 255.0) * 15)
        g = int((g / 255.0) * 15)
        b = int((b / 255.0) * 15)
        return (a << 12) | (r << 8) | (g << 4) | b

class pt(object):
    def __init__(self):
        self.t = {}
        self.i = []
    def add(self, n):
        if n in self.t:
            return self.t[n]
        else:
            m = len(self.i)
            self.i.append(n)
            self.t[n] = m
            return m

def main():
    filename = sys.argv[1]
    # filename, x, y = filename.rpartition('.')
    ifn = filename + '.rgba'
    ofn = filename + '.btiu'
    f = open(ofn, 'wb')
    f.write(head)

    ptl = pt()

    f2 = open(ifn, 'rb')
    w = 48
    h = 48
    bw = 8
    bh = 4

    for y in xrange(0, h, bh):
        for x in xrange(0, w, bw):
            for by in xrange(bh):
                offs = ((y+by)*w + x) * 4
                f2.seek(offs)
                for bx in xrange(bw):
                    p = struct.unpack('BBBB', f2.read(4))
                    m = rgb5a3(p)
                    d = ptl.add(m)
                    f.write(struct.pack('>B', d))

    assert f.tell() == 0x920
    for i in ptl.i:
        f.write(struct.pack('>H', i))
    print len(ptl.i)

    f.seek(0xa)
    f.write(struct.pack('>H', len(ptl.i)))

main()
