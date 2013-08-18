#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 18/08/2013

@author: piranna
'''

from itertools import count
from os        import renames
from os.path   import exists, join, splitext
from re        import sub


CONFLICT_REGEX = [r' \(Case Conflict( \(\d+\))?\)',
                  r' \(Conflicto de mayúsculas y minúsculas( \(\d+\))?\)',
                  r' \(Copia en conflicto de .+? \d{4}-\d{2}-\d{2}\)']


def genNonConflictingPath(path):
    root, ext = splitext(path)

    for index in count(1):
        newPath = root+' ('+str(index)+')'+ext

        if not exists(newPath):
            return newPath


def fixConflict(root, oldPath):
    path = oldPath

    for regex in CONFLICT_REGEX:
        path = sub(regex, '', path)

    newPath = join(root, path)

    if newPath == oldPath:
        return

    if exists(newPath):
        newPath = genNonConflictingPath(newPath)

    renames(oldPath, newPath)

    print oldPath
    print newPath
    print


if __name__ == '__main__':
    from argparse import ArgumentParser
    from os       import removedirs, walk
    from os.path  import abspath

    parser = ArgumentParser()
    parser.add_argument('dirs', nargs='+')

    args = parser.parse_args()

    root = abspath(args.dirs[0])

    for arg_dir in args.dirs:
        for dirpath, dirnames, filenames in walk(arg_dir):

            # Conflicted files
            for name in filenames:
                fixConflict(root, join(dirpath, name))

            # Empty directories
            for name in dirnames:
                path = join(dirpath, name)

                try:
                    removedirs(path)
                except OSError:
                    pass
                else:
                    print '[Deleted]',path
