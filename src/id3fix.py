#!/usr/bin/env python

'''
Created on 08/08/2013

@author: piranna
'''

from collections import Counter, defaultdict

from mutagen.easyid3 import EasyID3
from mutagen.id3     import ID3NoHeaderError

from mp3hash import mp3hash


# Global tag values to improve fixing of conflicts
tags_values = defaultdict(Counter)


class Duplicate:
    def __init__(self):
        self._checked = set()

        self.files = {}
        self.commons = {}
        self.merge = {}
        self.conflicts = defaultdict(Counter)

    def _apply(self, key, value):
        for id3 in self.files.itervalues():
            # Updage global tags counter
            try:
                old_value = id3[key]
            except KeyError:
                old_value = None

            tags = tags_values[key]

            if old_value:
                tags.subtract(old_value)
            tags.update(value)

            # Set the (new) entry value
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

            if value:
                tags_values[key].update(value)


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

    def fix(self, user_feedback):
        self.fixMerge()
        self.fixConflicts(user_feedback)

    def fixMerge(self):
        # Apply the ready-to-merge values to the tags
        for duplicate in self.itervalues():
            merge = duplicate.merge

            for key, value in merge.iteritems():
                duplicate._apply(key, value)

            # Set the merge values as common
            duplicate._setCommon(merge)

    def fixConflicts(self, user_feedback):
        conflictsQueue = []
        askUser = False

        def getMostCommons(most_common):
            value_0, counts_0 = most_common[0]
            result = [value_0]

            for value, counts in most_common[1:]:
                if counts < counts_0:
                    break
                result.append(value)

            return result

        def _fixConflicts(duplicates):
            for duplicate in duplicates:

                addedToQueue = False

                def fixConflict(key, conflict):
                    # Get the most common values
                    most_common = getMostCommons(conflict.most_common())

                    # More than one is the most common, select one
                    if len(most_common) > 1:
                        # Select the global most common value
                        tags = tags_values[key]

                        values = {}
                        for value in most_common:
                            values[value] = tags[value]
                        values = Counter(values)

                        most_common = getMostCommons(values.most_common())

                        # More than one is still the most common,
                        # queue it to re-check later
                        if len(most_common) > 1:
                            # Add duplicate to queue only once on this round
                            if not addedToQueue:
                                if askUser:
                                    files = duplicate.files.iterkeys()
                                    value = user_feedback(files, values)

                                    askUser = False

                                else:
                                    conflictsQueue.append(duplicate)
                                    addedToQueue = True

                            return

                    # Only one is the most common, use it
                    value = most_common[0]

                    duplicate._apply(key, value)

                    # Set the conflicts values as common
                    duplicate.commons[key] = value
                    del duplicate.conflicts[key]

                for key, conflict in duplicate.conflicts.items():
                    fixConflict(key, conflict)

        # Run initially over the duplicates list, and later over the unresolved
        # conflicts (if any)
        duplicates = self.itervalues()
        length = len(self._hashes)
        while duplicates:
            _fixConflicts(duplicates)

            # If number of items in the queue has not decreased (probably) means
            # no conflicts could be resolved also after several iterations, so
            # we ask to the user
            if len(conflictsQueue) == length:
                askUser = True

            # Update duplicates and conflicts queues
            duplicates = conflictsQueue
            length = len(duplicates)
            conflictsQueue = []

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

    def user_feedback(files, values):
        print "Unsolvable conflict:"

        for file in files:
            print file
        print

        for index, value in enumerate(values, 1):
            print "\t["+index+"]",value
        print

        length = len(values)
        index = None

        while index not in xrange(1, length+1):
            index = raw_input("Select one option [1-"+length+"]:")

        return values[index]

    id3fix.fix(user_feedback)
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
