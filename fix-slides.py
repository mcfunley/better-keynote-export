#!/usr/bin/env python
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import os
from glob import glob
import appscript
from argparse import ArgumentParser
from contextlib import closing


class SlideFixer(object):
    def __init__(self, keynote, outdir, pagesize, font_size, notespace):
        self.keynote = os.path.abspath(keynote)
        self.outdir = os.path.abspath(outdir)
        self.pagesize = pagesize
        self.notes = None
        self.font_size = font_size
        self.notespace = notespace

    def run(self):
        print 'Processing', self.keynote
        self.make_dirs()
        self.export()
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
        s.fontSize = self.font_size
        s.leading = 1.2 * self.font_size

        img_w, img_h = self.pagesize
        pagesize = (img_w, img_h + self.notespace)

        c = canvas.Canvas(self.outfile, pagesize=pagesize)
        c.setFont('Courier', 80)
        c.setStrokeColorRGB(0,0,0)

        for slide, note in zip(glob('%s/*jpeg' % self.slidesdir), self.notes):
            # fill the page with white
            c.setFillColor(HexColor('#ffffff'))
            c.rect(0, 0, img_w, img_h + self.notespace, fill=1)

            c.drawImage(slide, 0, self.notespace, img_w, img_h, preserveAspectRatio=True)
            c.line(0, self.notespace, img_w, self.notespace)

            if note:
                p = Paragraph(note.replace('\n', '<br/>'), s)
                p.wrapOn(c, img_w - 20, self.notespace)
                p.breakLines(img_w - 20)
                p.drawOn(c, 10, self.notespace - 10)
            c.showPage()
        c.save()


    def export(self):
        keynote = appscript.app('Keynote')
        outpath = appscript.mactypes.File(self.slidesdir)
        k = appscript.k
        keynote_file = appscript.mactypes.File(self.keynote)
        with closing(keynote.open(keynote_file)) as doc:
            self.notes = doc.slides.presenter_notes()

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
    ap.add_argument('-k', '--keynote', help="Path to the keynote to convert",
                    required=True)
    ap.add_argument('-o', '--outdir', help="Where to put the output.",
                    required=True)
    ap.add_argument('-p', '--pagesize', help='The size of the pages.',
                    default='1920x1080')
    ap.add_argument('-f', '--font-size', help='Font size for notes',
                    type=int, dest='font_size', default=36)
    ap.add_argument('-s', '--notespace', help='Height of space for notes',
                    type=int, dest='notespace', default=256)

    args = ap.parse_args()
    pagesize = tuple([int(s) for s in args.pagesize.split('x')])

    SlideFixer(args.keynote, args.outdir, pagesize,
               args.font_size, args.notespace).run()


if __name__ == '__main__':
    main()
