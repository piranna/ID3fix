#!/usr/bin/env python

'''
Created on 08/08/2013

@author: piranna
'''

from collections import Counter, defaultdict

from mp3hash         import mp3hash
from mutagen.easyid3 import EasyID3


class Duplicate:
    def __init__(self):
        self._files = set()
        self._commons = {}
        self._merge = {}
        self._conflicts = defaultdict(set)

    def _checkEntry(self, key, value):
        ""

        # Key has not value, check if it was found before so it should be merged
        if not value:
            try:
                value = self._commons.pop(key)
            except KeyError:
                pass
            else:
                self._merge[key] = value

        #
        elif key in self._conflicts:
            self._conflicts[key].add(value)

        elif key in self._merge:
            if value != self._merge[key]:
                self._conflicts[key].add(self._merge.pop(key), value)

        elif key in self._commons:
            if value != self._commons[key]:
                self._conflicts[key].add(self._commons[key].pop(), value)

        # Key is new
        else:
            self._commons[key] = value


    def add(self, path):
        id3 = EasyID3(path)

        for key in id3.valid_keys.iterkeys():
            self._checkEntry(key, id3[key])


class Id3fix:
    def __init__(self):
        self._hashes = defaultdict(Duplicate)

    def add(self, path):
        file_hash = mp3hash(path)

        if(file_hash):
            self._hashes[file_hash].add(path)

    def __iter__(self):
        return self._hashes


if __name__ == '__main__':
    from argparse import ArgumentParser
    from os       import walk
    from os.path  import join

    parser = ArgumentParser()
    parser.add_argument('dirs', nargs='+')

    args = parser.parse_args()

    id3fix = Id3fix()

    for arg_dir in args.dirs:
        for dirpath, dirnames, filenames in walk(arg_dir):
            for name in filenames:
                id3fix.add(join(dirpath, name))

    for duplicate in id3fix:
        print duplicate
