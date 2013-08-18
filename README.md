ID3fix - fix metadata on MP3 files
==================================

Utility to fix metadata on duplicated MP3 files. It's ideal for when you have
duplicated music files with the same audio but with diferent metadata, so
duplicate files detectors see them as diferent ones.

Currently it's terrible slow... but does it's job :-) I have plans to speed it,
but until them, do the checks on small batchs.

To-Do
=====
* Speed-Ups
** Use Mutagen for hashing, so only files are open once
** Do a first check by size instead of doing directly the hash

* Other functionality
** Add options to enable functionality independently
** Allow to delete duplicated files after filling metadata (no need of 'fdupes')
** Use ID3 instead of EasyID3 to have access to all the tags