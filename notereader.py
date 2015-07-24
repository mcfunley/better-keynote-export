#!/usr/bin/env python
import snappy
import os
from zipfile import ZipFile
import tempfile
import shutil
from contextlib import nested, contextmanager



@contextmanager
def tempdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)
    


class NoteReader(object):
    def read(self, keynote_file):
        index_file = os.path.join(keynote_file, 'Index.zip')
        notes = []
        with nested(ZipFile(index_file, 'r'), tempdir()) as (z, d):
            for slide in self.slides(z):
                notes.append(self.get_notes(z, slide, d))
        return notes
                

    def slides(self, index_zip):
        files = sorted(index_zip.namelist())
        for f in files:
            if f.startswith('Index/Slide'):
                yield f
                             

    def get_notes(self, index_zip, slide_name, temp_dir):
        data = index_zip.read(slide_name)
        print len(data)



if __name__ == '__main__':
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument('-k', '--keynote', help="Path to the keynote")
    args = ap.parse_args()
    for n in NoteReader().read(args.keynote):
        pass
