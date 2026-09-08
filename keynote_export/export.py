#!/usr/bin/env python
import itertools
import os
import shutil
from contextlib import closing
from glob import glob
from typing import Optional

import appscript
import click
from jinja2 import Environment, FileSystemLoader
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

RESOURCES = os.path.join(os.path.dirname(__file__), "resources")

SRCSET_WIDTHS = (480, 960, 1440, 1920)
WEBP_QUALITY = 80

# Slides sit two-to-a-row until the 700px breakpoint in presentation.css, below
# which they stack. The subtractions are the surrounding padding.
SLIDE_SIZES = "(max-width: 700px) calc(100vw - 20px), calc(50vw - 60px)"

sf = TTFont("SanFrancisco", f"{RESOURCES}/SanFrancisco-Regular.ttf")
pdfmetrics.registerFont(sf)


class Options(object):
    def __init__(
        self, outdir, pagesize, font_size, title, bsky_handle, mastodon_handle, skip_builds
    ):
        self.outdir = os.path.abspath(outdir)
        self.pagesize = pagesize
        self.font_size = font_size
        self.leading = 1.2 * font_size
        self.notepadding = 10
        self.font = "SanFrancisco"
        self.title = title
        self.bsky_handle = bsky_handle
        self.mastodon_handle = mastodon_handle
        self.skip_builds = skip_builds

    @property
    def slidesdir(self):
        return os.path.join(self.outdir, "slides")

    @property
    def note_width(self):
        w, _ = self.pagesize
        return w - self.notepadding * 2


def slides_and_notes(opts, notes):
    return zip(sorted(glob("%s/*jpeg" % opts.slidesdir)), notes)


def variant_widths(native_width):
    """The widths to render a slide at, narrowest first. Never upscales."""
    return [w for w in SRCSET_WIDTHS if w < native_width] + [native_width]


def srcset(variants):
    return ", ".join("%s %dw" % (path, w) for path, w in variants)


def generate_images(opts, notes):
    """Render each exported slide to webp at the srcset widths.

    Keynote only exports jpeg, and the PDF is drawn from those, so this has to
    run after generate_pdf. The originals are deleted once the webps exist,
    since only the webps are published.
    """
    slides = []

    for jpeg, note in slides_and_notes(opts, notes):
        with Image.open(jpeg) as img:
            width, height = img.size
            stem = os.path.splitext(jpeg)[0]

            variants = []
            for w in variant_widths(width):
                path = "%s-%d.webp" % (stem, w)
                rendition = (
                    img
                    if w == width
                    else img.resize(
                        (w, round(height * w / width)), Image.LANCZOS
                    )
                )
                rendition.save(path, "WEBP", quality=WEBP_QUALITY, method=6)
                variants.append((path, w))

        os.remove(jpeg)
        slides.append(
            {"variants": variants, "width": width, "height": height, "note": note}
        )

    return slides


def make_dirs(opts):
    for d in (
        opts.outdir,
        opts.slidesdir,
    ):
        if not os.path.isdir(d):
            os.mkdir(d)


def generate_pdf(opts, notes):
    outfile = os.path.join(opts.outdir, "out.pdf")

    tallest_note = -1
    for n in notes:
        lines = simpleSplit(n, opts.font, opts.font_size, opts.note_width)
        tallest_note = max(tallest_note, len(lines))

    note_height = ((tallest_note + 1) * opts.leading) + (opts.notepadding * 2)

    s = ParagraphStyle("note")
    s.fontName = opts.font
    s.textColor = "black"
    s.alignment = TA_LEFT
    s.fontSize = opts.font_size
    s.leading = opts.leading

    img_w, img_h = opts.pagesize
    pagesize = (img_w, img_h + note_height)

    c = canvas.Canvas(outfile, pagesize=pagesize)
    c.setStrokeColorRGB(0, 0, 0)

    for slide, note in slides_and_notes(opts, notes):
        c.setFillColor(HexColor("#ffffff"))
        c.rect(0, 0, img_w, img_h + note_height, fill=1)

        c.drawImage(
            slide, 0, note_height, img_w, img_h, preserveAspectRatio=True
        )
        c.line(0, note_height, img_w, note_height)

        if note:
            p = Paragraph(note.replace("\n", "<br/>"), s)
            p.wrapOn(c, opts.note_width, note_height)
            p.breakLines(opts.note_width)
            p.drawOn(c, opts.notepadding, note_height - opts.notepadding)
        c.showPage()
    c.save()


def export_keynote(filename, opts):
    filename = os.path.abspath(filename)

    keynote = appscript.app("Keynote")
    outpath = appscript.mactypes.File(opts.slidesdir)
    k = appscript.k
    keynote_file = appscript.mactypes.File(filename)

    with closing(keynote.open(keynote_file)) as doc:
        notes = doc.slides.presenter_notes()
        skipped = doc.slides.skipped()
        notes = list(itertools.compress(notes, [not s for s in skipped]))

        doc.export(
            as_=k.slide_images,
            to=outpath,
            with_properties={
                k.export_style: k.IndividualSlides,
                k.compression_factor: 0.9,
                k.image_format: k.JPEG,
                k.all_stages: not opts.skip_builds,
                k.skipped_slides: False,
            },
        )

    return notes

def generate_html(opts, slides):
    def imgpath(s):
        return s.replace(opts.outdir + "/", "")

    def rendered(slide):
        variants = [(imgpath(p), w) for p, w in slide["variants"]]
        return {
            "src": variants[-1][0],
            "srcset": srcset(variants),
            "width": slide["width"],
            "height": slide["height"],
            "note": slide["note"],
        }

    e = Environment(loader=FileSystemLoader(RESOURCES))
    t = e.get_template("site.jinja")

    s = t.render(
        slides=[rendered(s) for s in slides],
        sizes=SLIDE_SIZES,
        title=opts.title,
        bsky_handle=opts.bsky_handle,
        mastodon_handle=opts.mastodon_handle,
    )

    outfile = os.path.join(opts.outdir, "index.html")
    open(outfile, "w").write(s)

    shutil.copyfile(
        f"{RESOURCES}/presentation.css",
        os.path.join(opts.outdir, "presentation.css"),
    )

@click.command()
@click.option(
    "-k",
    "--keynote",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path to the keynote to convert",
    required=True,
)
@click.option(
    "-o",
    "--outdir",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Where to put the output.",
    required=True,
)
@click.option(
    "-p",
    "--pagesize",
    default="1920x1080",
    help="The size of the pages.",
    type=click.STRING,
)
@click.option(
    "-f",
    "--font-size",
    type=click.INT,
    help="Font size for notes",
    default=36,
)
@click.option("-t", "--title", help="Title of the presentation", required=True)
@click.option(
    "-u",
    "--bluesky-handle",
    help="BlueSky handle for author",
    required=False,
    type=click.STRING,
)
@click.option(
    "-m",
    "--mastodon-handle",
    help="Mastodon handle for author",
    required=False,
    type=click.STRING,
)
@click.option(
    "--skip-builds", is_flag=True, help="Skip build stages", default=False
)
def main(
    keynote: str,
    outdir: str,
    pagesize: str,
    font_size: int,
    title: str,
    bluesky_handle: Optional[str],
    mastodon_handle: Optional[str],
    skip_builds: bool,
):
    pagesize = tuple([int(s) for s in pagesize.split("x")])
    opts = Options(
        outdir,
        pagesize,
        font_size,
        title,
        bluesky_handle,
        mastodon_handle,
        skip_builds,
    )

    print("Processing", keynote)
    make_dirs(opts)
    notes = export_keynote(keynote, opts)
    generate_pdf(opts, notes)
    generate_html(opts, generate_images(opts, notes))


if __name__ == "__main__":
    main()
