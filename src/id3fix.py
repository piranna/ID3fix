#!/usr/bin/env python

'''
Created on 08/08/2013

@author: piranna
'''

from collections import Counter, defaultdict

from mutagen.easyid3 import EasyID3
from mutagen.id3     import ID3NoHeaderError

from mp3hash import mp3hash


class Duplicate:
    def __init__(self):
        self._checked = set()

        self.files = {}
        self.commons = {}
        self.merge = {}
        self.conflicts = defaultdict(Counter)

    def _apply(self, key, value):
        for id3 in self.files.itervalues():
            id3[key] = value

    def _checkEntry(self, key, value):
        ""

        def setConflict(key, value):
            self.conflicts[key].update(value)

        # Key has not value, check if it was found before so it should be merged
        if not value:
            value = self.commons.pop(key, None)

            if value:
                self.merge[key] = value

        # Key had conflicts, add another one more
        elif key in self.conflicts:
            setConflict(key, value)

        # Key could be merged, check for conflicts
        elif key in self.merge:
            if value != self.merge[key]:
                setConflict(key, self.merge.pop(key))
                setConflict(key, value)

        # Key common to all copies, check for conflicts
        elif key in self.commons:
            if value != self.commons[key]:
                setConflict(key, self.commons.pop(key))
                setConflict(key, value)

        # Check if key was checked before, so it should be merged
        elif key in self._checked:
            self.merge[key] = value

        # Key is new, set as common
        else:
            self.commons[key] = value

        # Set key as checked
        self._checked.add(key)

    def _setCommon(self, merged):
        self.commons.update(merged)
        merged.clear()

    def add(self, path, id3):
        self.files[path] = id3

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

    def fix(self):
        self.fixMerge()
        self.fixConflicts()

    def fixMerge(self):
        # Apply the ready-to-merge values to the tags
        for duplicate in self.itervalues():
            merge = duplicate.merge

            for key, value in merge.iteritems():
                duplicate._apply(key, value)

            # Set the merge values as common
            duplicate._setCommon(merge)

    def fixConflicts(self):
        for duplicate in self.itervalues():
            conflicts = duplicate.conflicts

            for key, conflict in conflicts.iteritems():
                value = conflict.most_common(1)[0][0]

                duplicate._apply(key, value)

            # Set the conflicts values as common
            duplicate._setCommon(conflicts)

    def itervalues(self):
        return self._hashes.itervalues()

    def save(self):
        for duplicate in self.itervalues():
            for id3 in duplicate.files.itervalues():
                id3.save(v1=2)


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

    id3fix.fixMerge()
    id3fix.save()

    for duplicate in id3fix.itervalues():
        if(len(duplicate.files) > 1):
            print "Files:", duplicate.files.keys()
#            print "Commons", duplicate.commons
            if duplicate.merge:
                print "Merge:", duplicate.merge
            if duplicate.conflicts:
                print "Conflicts", duplicate.conflicts
            print
