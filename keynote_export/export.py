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
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

RESOURCES = os.path.join(os.path.dirname(__file__), "resources")

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


def generate_html(opts, notes):
    def imgpath(s):
        return s.replace(opts.outdir + "/", "")

    e = Environment(loader=FileSystemLoader(RESOURCES))
    t = e.get_template("site.jinja")

    s = t.render(
        slides=[
            {"image": imgpath(s), "note": n}
            for s, n in slides_and_notes(opts, notes)
        ],
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
    generate_html(opts, notes)


if __name__ == "__main__":
    main()
