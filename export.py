#!/usr/bin/env python
import appscript
from argparse import ArgumentParser
from contextlib import closing
from glob import glob
from jinja2 import Environment, FileSystemLoader
import math
import os
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
import shutil


sf = TTFont('SanFrancisco', 'resources/SanFrancisco-Regular.ttf')
pdfmetrics.registerFont(sf)


class Options(object):
    def __init__(self, outdir, pagesize, font_size, title, twitter_username):
        self.outdir = os.path.abspath(outdir)
        self.pagesize = pagesize
        self.font_size = font_size
        self.leading = 1.2 * font_size
        self.notepadding = 10
        self.font = 'SanFrancisco'
        self.title = title
        self.twitter_username = twitter_username

    @property
    def slidesdir(self):
        return os.path.join(self.outdir, 'slides')

    @property
    def note_width(self):
        w, _ = self.pagesize
        return w - self.notepadding * 2


def slides_and_notes(opts, notes):
    return zip(sorted(glob('%s/*jpeg' % opts.slidesdir)), notes)


def make_dirs(opts):
    for d in (opts.outdir, opts.slidesdir,):
        if not os.path.isdir(d):
            os.mkdir(d)


def generate_pdf(opts, notes):
    outfile = os.path.join(opts.outdir, 'out.pdf')

    tallest_note = -1
    for n in notes:
        lines = simpleSplit(n, opts.font, opts.font_size, opts.note_width)
        tallest_note = max(tallest_note, len(lines))

    note_height = ((tallest_note + 1) * opts.leading) + (opts.notepadding * 2)

    s = ParagraphStyle('note')
    s.fontName = opts.font
    s.textColor = 'black'
    s.alignment = TA_LEFT
    s.fontSize = opts.font_size
    s.leading = opts.leading

    img_w, img_h = opts.pagesize
    pagesize = (img_w, img_h + note_height)

    c = canvas.Canvas(outfile, pagesize=pagesize)
    c.setStrokeColorRGB(0, 0, 0)

    for slide, note in slides_and_notes(opts, notes):
        c.setFillColor(HexColor('#ffffff'))
        c.rect(0, 0, img_w, img_h + note_height, fill=1)

        c.drawImage(slide, 0, note_height, img_w, img_h, preserveAspectRatio=True)
        c.line(0, note_height, img_w, note_height)

        if note:
            p = Paragraph(note.replace('\n', '<br/>'), s)
            p.wrapOn(c, opts.note_width, note_height)
            p.breakLines(opts.note_width)
            p.drawOn(c, opts.notepadding, note_height - opts.notepadding)
        c.showPage()
    c.save()


def export_keynote(filename, opts):
    filename = os.path.abspath(filename)

    keynote = appscript.app('Keynote')
    outpath = appscript.mactypes.File(opts.slidesdir)
    k = appscript.k
    keynote_file = appscript.mactypes.File(filename)

    with closing(keynote.open(keynote_file)) as doc:
        notes = doc.slides.presenter_notes()

        doc.export(as_=k.slide_images, to=outpath, with_properties = {
            k.export_style: k.IndividualSlides,
            k.compression_factor: 0.9,
            k.image_format: k.JPEG,
            k.all_stages: True,
            k.skipped_slides: False
        })

    return notes


def generate_html(opts, notes):
    def imgpath(s):
        return s.replace(opts.outdir + '/', '')

    e = Environment(loader=FileSystemLoader('resources'))
    t = e.get_template('site.jinja')

    s = t.render(slides=[
        { 'image': imgpath(s), 'note': n }
        for s, n in slides_and_notes(opts, notes)
    ], title=opts.title, twitter_username=opts.twitter_username)

    outfile = os.path.join(opts.outdir, 'index.html')
    open(outfile, 'w').write(s)

    shutil.copyfile(
        'resources/presentation.css',
        os.path.join(opts.outdir, 'presentation.css')
    )


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
    ap.add_argument('-t', '--title', help='Title of the presentation')
    ap.add_argument('-u', '--twitter-username', help='Twitter for author',
                    dest='twitter_username')

    args = ap.parse_args()
    pagesize = tuple([int(s) for s in args.pagesize.split('x')])
    opts = Options(args.outdir, pagesize, args.font_size, args.title,
                   args.twitter_username)

    print('Processing', args.keynote)
    make_dirs(opts)
    notes = export_keynote(args.keynote, opts)
    generate_pdf(opts, notes)
    generate_html(opts, notes)


if __name__ == '__main__':
    main()
