#!/usr/bin/env python
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import sys
import os
from glob import glob
import appscript
from argparse import ArgumentParser
from contextlib import closing
from notereader import NoteReader


class SlideFixer(object):
    def __init__(self, keynote, notes, outdir, pagesize):
        self.keynote = os.path.abspath(keynote)
        self.notes = notes
        self.outdir = os.path.abspath(outdir)
        self.pagesize = pagesize

    def run(self):
        print 'Processing', self.keynote

        self.make_dirs()
        #self.export()
        self.emit_pdf()

    @property
    def slidesdir(self):
        return os.path.join(self.outdir, 'slides')

    @property
    def outfile(self):
        return os.path.join(self.outdir, 'out.pdf')

    def make_dirs(self):
        for d in (self.outdir, self.slidesdir,):
            if not os.path.isdir(d):
                os.mkdir(d)

    def emit_pdf(self):
        s = ParagraphStyle('note')
        s.textColor = 'black'
        s.alignment = TA_LEFT
        s.fontSize = 24
        s.leading = 24

        notespace = 256
        img_w, img_h = self.pagesize
        pagesize = (img_w, img_h + notespace)

        c = canvas.Canvas(self.outfile, pagesize=pagesize)
        c.setFont('Courier', 80)
        c.setStrokeColorRGB(0,0,0)

        for slide, note in zip(glob('%s/*jpeg' % self.slidesdir), self.notes):
            c.drawImage(slide, 0, notespace, img_w, img_h, preserveAspectRatio=True)
            c.line(0, notespace, img_w, notespace)
            if note:
                p = Paragraph(note.replace('\n', '<br/>'), s)
                p.wrapOn(c, img_w - 20, notespace)
                p.breakLines(img_w - 20)
                p.drawOn(c, 10, notespace - 10)
            c.showPage()
        c.save()


    def export(self):
        keynote = appscript.app('Keynote')
        outpath = appscript.mactypes.File(self.slidesdir)
        k = appscript.k
        keynote_file = appscript.mactypes.File(self.keynote)
        with closing(keynote.open(keynote_file)) as doc:
            doc.export(as_=k.slide_images, to=outpath, with_properties = {
                k.export_style: k.IndividualSlides,
                k.compression_factor: 0.9,
                k.image_format: k.JPEG,
                k.all_stages: True,
                k.skipped_slides: False
            })


def notes_from_file(fn, sep):
    return open(fn, 'r').read().split(sep)


def main():
    ap = ArgumentParser()
    ap.add_argument('-k', '--keynote', help="Path to the keynote to convert")
    ap.add_argument(
        '-n', '--notes-file', help="Path to the notes file.",
        default=None
    )
    ap.add_argument('-s', '--notes-file-separator', default=None)
    ap.add_argument('-o', '--outdir', help="Where to put the output.")
    ap.add_argument('-p', '--pagesize', help='The size of the pages.',
                    default='1920x1080')

    args = ap.parse_args()

    if args.notes_file:
        print 'Reading notes from file:', args.notes_file
        sep = args.notes_file_separator + '\n' or '\n\n'
        notes = notes_from_file(args.notes_file, sep)
    else:
        notes = NoteReader().read(args.keynote)

    pagesize = tuple([int(s) for s in args.pagesize.split('x')])

    SlideFixer(args.keynote, notes, args.outdir, pagesize).run()


if __name__ == '__main__':
    main()
