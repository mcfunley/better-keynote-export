#!/usr/bin/env python
import os
import shutil


class NoteReader(object):
    def read(self, keynote_file):
        return []


if __name__ == '__main__':
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument('-k', '--keynote', help="Path to the keynote")
    args = ap.parse_args()
    for n in NoteReader().read(args.keynote):
        pass
