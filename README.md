This is a crappy script that provides a fix for Keynote 13's "export with notes" formatting regression. Basically,

* This exports all of your slides as JPEG's.
* It does this using Applescript, so it is prone to break with new versions of Keynote.
* It compiles the JPEG's and the notes into a PDF with reasonably formatted notes.

One of my talks is provided here as a sample. To run the sample:

    ./fix-slides.py --keynote sample/scalding-at-etsy-v2.key --notes-file --outdir out

That should create `out/out.pdf`.
