#!/usr/bin/env python

import os
import os.path
import struct
import sys

def lw(f):
    x = f.read(4)
    return struct.unpack('>L', x)[0]

def ls(f):
    x = f.read(2)
    return struct.unpack('>H', x)[0]

def creat_open(fn):
    d = os.path.dirname(fn)
    try:
        os.makedirs(d)
    except:
        pass
    return open(fn, 'wb')

def rc0(f, o):
    oo = f.tell()
    f.seek(o, os.SEEK_SET)
    s = f.read(32)
    f.seek(oo, os.SEEK_SET)
    return s[:s.find('\0')]

def rst(f, o, s):
    f.seek(o, os.SEEK_SET)
    st = f.read(s)
    e = st.split('\0')
    t = {}
    i = 0
    for m in e:
        t[i] = m
        i += len(m) + 1
    return t

def nhash(S):
    H = 0
    m = 1
    for c in S[::-1]:
        H = (H + ord(c) * m) & 0xFFFF
        m *= 3
    return H

def copy(src, dest, offset, size):
    old = src.tell()
    src.seek(offset)
    dest.write(src.read(size))
    src.seek(old)

def ext(f, ext_path):
    magic = f.read(4)
    assert magic == "RARC"

    size = lw(f)
    header_off = lw(f)
    header_size = lw(f)
    f.seek(header_off, os.SEEK_SET)

    n_node = lw(f)
    root = lw(f)
    n_entry = lw(f)
    entry_off = lw(f)

    str_pool_size = lw(f)
    str_pool_off = lw(f)
    st = rst(f, header_off + str_pool_off, str_pool_size)

    data_off = header_off + header_size

    for i in xrange(n_node):
        f.seek(header_off + root + (i * 0x10), os.SEEK_SET)
        node_type = f.read(4)
        node_name_off = lw(f)
        node_name = st[node_name_off]
        node_name_hash = ls(f)
        node_n_entries = ls(f)
        node_entry_idx = lw(f)

        for j in xrange(node_n_entries):
            f.seek(header_off + entry_off + ((node_entry_idx + j) * 0x14), os.SEEK_SET)
            n = f.tell()
            entry_id = ls(f)
            entry_csum = ls(f)
            entry_mode = ls(f)
            if entry_mode not in (0x1100, 0x9500):
                continue
            entry_name_off = ls(f)

            entry_data_off = lw(f)
            entry_data_size = lw(f)
            entry_unk = lw(f)
            entry_fn = st[entry_name_off]

            fnpath = os.path.join(ext_path, node_name, entry_fn)
            with creat_open(fnpath) as out:
                copy(f, out, data_off + entry_data_off, entry_data_size)

def main():
    filename = sys.argv[1]
    f = open(filename, 'rb')
    path, x, y = filename.rpartition('.')
    path += '.d'
    ext(f, path)

main()
