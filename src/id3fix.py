#!/usr/bin/env python

'''
Created on 08/08/2013

@author: piranna
'''

from collections import Counter, defaultdict

from mp3hash         import mp3hash
from mutagen.easyid3 import EasyID3
from mutagen.id3     import ID3NoHeaderError


class Duplicate:
    def __init__(self):
        self.files = set()
        self.commons = {}
        self.merge = {}
        self.conflicts = defaultdict(set)

    def _checkEntry(self, key, value):
        ""

        def setConflict(key, value):
            self.conflicts[key].add(tuple(value))


        # Key has not value, check if it was found before so it should be merged
        if not value:
            try:
                value = self.commons.pop(key)
            except KeyError:
                pass
            else:
                print "Merge:", self.files, key, value
                self.merge[key] = value

        #
        elif key in self.conflicts:
            print "Conflic:", self.files, key, value, self.conflicts[key]
            setConflict(key, value)

        elif key in self.merge:
            if value != self.merge[key]:
                print "Conflic:", self.files, key, value, self.merge[key]
                setConflict(key, self.merge.pop(key))
                setConflict(key, value)

        elif key in self.commons:
            if value != self.commons[key]:
                print "Conflic:", self.files, key, value, self.commons[key]
                setConflict(key, self.commons.pop(key))
                setConflict(key, value)

        # Key is new
        else:
            self.commons[key] = value


    def add(self, path, id3):
        self.files.add(path)

        for key in id3.valid_keys.iterkeys():
            try:
                value = id3[key]
            except KeyError:
                value = None

            self._checkEntry(key, value)


class Id3fix:
    def __init__(self):
        self._hashes = defaultdict(Duplicate)

    def add(self, path):
        file_hash = mp3hash(path)

        if(file_hash):
            try:
                id3 = EasyID3(path)
            except (ID3NoHeaderError, ValueError):
                return

            self._hashes[file_hash].add(path, id3)

    def itervalues(self):
        return self._hashes.itervalues()


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

    for duplicate in id3fix.itervalues():
        if(len(duplicate.files) > 1):
            print "Files:", duplicate.files
            print "Commons", duplicate.commons
            print "Merge:", duplicate.merge
            print "Conflicts", duplicate.conflicts
            print
