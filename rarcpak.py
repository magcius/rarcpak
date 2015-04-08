#!/usr/bin/env python

import os
import os.path
import struct
import sys

def align(n):
    return (n + 0x1f) & ~0x1f
def pad(f):
    p = f.tell()
    ap = align(p)
    pad = ap - p
    f.write('\0' * pad)
    return ap

def nhash(S):
    H = 0
    m = 1
    for c in S[::-1]:
        H = (H + ord(c) * m) & 0xFFFF
        m *= 3
    return H

class strt(object):
    def __init__(self):
        self.track = {}
        self.items = []
        self.size = 0
        self.add('.')
        self.add('..')
    def add(self, s):
        if s in self.track:
            return self.track[s]
        else:
            self.items.append(s)
            self.track[s] = self.size
            self.size += len(s) + 1
            return self.track[s]
    def serialize(self, f):
        f.write('\0'.join(self.items))

def dirent(st, name, offs):
    return dict(entry_id=0xFFFF,
                name=name,
                name_offs=st.add(name),
                nhash=nhash(name),
                mode=0x200,
                data_offs=offs,
                data_size=16)

def scan(st, p):
    nodes = []
    entries = []

    entry_id_map = { '': 0xFFFFFFFF, p: 0 }
    dir_id = 1

    for dirpath, dirs, filenames in os.walk(p):
        dirname = os.path.basename(dirpath)
        if dirpath == p:
            dirname = dirname.replace('.d', '')
            node_name = 'ROOT'
        else:
            node_name = dirname[:4].upper()

        entry_idx = len(entries)

        name_offs = st.add(dirname)

        for subdir in dirs:
            entry_id_map[os.path.join(dirpath, subdir)] = dir_id
            entries.append(dirent(st, subdir, dir_id))
            dir_id += 1

        for fn in sorted(filenames, key=lambda n: n.replace('_', '\xff')):
            path = os.path.join(dirpath, fn)
            entry = dict(entry_id=len(entries),
                         name=fn,
                         path=path,
                         name_offs=st.add(fn),
                         nhash=nhash(fn),
                         mode=0x9500,
                         data_offs=0,
                         data_size=0)
            entries.append(entry)

        entries.append(dirent(st, '.', entry_id_map[dirpath]))
        entries.append(dirent(st, '..', entry_id_map[os.path.dirname(dirpath)]))

        node = dict(dirname=dirname,
                    name=node_name,
                    name_offs=name_offs,
                    nhash=nhash(dirname),
                    entry_idx=entry_idx,
                    n_entries=len(entries) - entry_idx)
        nodes.append(node)

    return nodes, entries

def pak(f, ext_path):
    st = strt()
    nodes, entries = scan(st, ext_path)

    f.write('RARC')
    f.write('\0\0\0\0') # size
    f.write('\0\0\0\x20') # header off
    f.write('\0\0\0\0') # header size
    f.write('\0\x02\xa1\xc0')
    f.write('\0\x02\xa1\xc0')
    f.write('\0\0\0\0')
    f.write('\0\0\0\0')

    f.write(struct.pack('>L', len(nodes)))
    f.write('\0\0\0\x20') # root
    f.write(struct.pack('>L', len(entries)))
    f.write(struct.pack('>L', len(nodes) * 0x20)) # entry_off

    f.write('\0\0\0\0') # str_pool_size
    f.write('\0\0\0\0') # str_pool_off
    f.write(struct.pack('>H', len(entries)))
    f.write('\x01\x00')
    f.write('\0\0\0\0')

    for node in nodes:
        f.write(node['name'])
        f.write(struct.pack('>LHHL',
                            node['name_offs'],
                            node['nhash'],
                            node['n_entries'],
                            node['entry_idx']))
    for entry in entries:
        entry['backpatch'] = f.tell()
        f.write(struct.pack('>HHHHLL',
                            entry['entry_id'],
                            entry['nhash'],
                            entry['mode'],
                            entry['name_offs'],
                            entry['data_offs'],
                            entry['data_size']))
        f.write('\0\0\0\0')

    stoffs = pad(f)
    st.serialize(f)
    dtbegin = pad(f)
    f.seek(0x30, os.SEEK_SET)
    f.write(struct.pack('>LL', dtbegin - stoffs, stoffs - 0x20))

    f.seek(0x0C, os.SEEK_SET)
    f.write(struct.pack('>L', dtbegin - 0x20))
    f.seek(0, os.SEEK_END)

    for entry in entries:
        if entry['mode'] == 0x200:
            continue

        dtoffs = pad(f)
        dest = open(entry['path'], 'rb')
        f.write(dest.read())
        dest.close()
        end = f.tell()

        f.seek(entry['backpatch'] + 0x8, os.SEEK_SET)
        f.write(struct.pack('>LL', dtoffs - dtbegin, end - dtoffs))
        f.seek(end, os.SEEK_SET)

    end = pad(f)
    f.seek(0x4, os.SEEK_SET)
    f.write(struct.pack('>L', end))

def main():
    filename = sys.argv[1]
    path, x, y = filename.rpartition('.')
    path += '.d'

    filename += '2' # xxx
    f = open(filename, 'wb')
    pak(f, path)

main()
