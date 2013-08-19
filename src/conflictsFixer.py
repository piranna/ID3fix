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


CONFLICT_REGEX = [r' \(\d+\)',
                  r' \(Case Conflict\)',
                  r' \(Conflicto de mayúsculas y minúsculas\)',
                  r' \(Copia en conflicto de .+? \d{4}-\d{2}-\d{2}\)']


def genNonConflictingPath(newPath, oldPath):
    root, ext = splitext(newPath)

    for index in count(1):
        newPath = root+' ('+str(index)+')'+ext

        if newPath == oldPath:
            return

        if not exists(newPath):
            return newPath


def fixConflict(root, oldRoot, oldPath):
    newPath = oldPath
    oldPath = join(oldRoot, oldPath)

    for regex in CONFLICT_REGEX:
        newPath = sub(regex, '', newPath)

    newPath = join(root, newPath)

    if newPath == oldPath:
        return

    if exists(newPath):
        newPath = genNonConflictingPath(newPath, oldPath)

    if newPath:
        renames(oldPath, newPath)
        print '[Renamed]',oldPath,'=>',newPath


if __name__ == '__main__':
    from argparse import ArgumentParser
    from os       import removedirs, walk
    from os.path  import abspath, commonprefix, dirname, relpath

    parser = ArgumentParser()
    parser.add_argument('dirs', nargs='+')

    args = parser.parse_args()

    # Set all paths as absolute ones
    for index, arg_dir in enumerate(args.dirs):
        args.dirs[index] = abspath(arg_dir)

    root = args.dirs[0]

    for arg_dir in args.dirs:
        for dirpath, dirnames, filenames in walk(arg_dir):
            path = relpath(dirpath, arg_dir)

            # Conflicted files
            for name in filenames:
                fixConflict(root, arg_dir, join(path, name))

#             # Empty directories
#             for name in dirnames:
#                 path = join(dirpath, name)
#
#                 try:
#                     removedirs(path)
#                 except OSError:
#                     pass
#                 else:
#                     print '[Deleted]',path
