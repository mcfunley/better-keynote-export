This is a crappy script that provides a fix for Keynote 13's "export with notes" regression. I've only used it for my own work and you'll probably have to mess with it to get it to do anything else. Basically,

* This exports all of your slides as JPEG's.
* It does this using Applescript, so it is finicky as hell.
* You have to put all of your speaker notes into a text file (put two newlines between each slide). Sorry, I couldn't figure out how to isolate the speaker notes in the keynote file. Pull requests welcome!
* It compiles the JPEG's and the notes into a PDF with reasonably formatted notes.

One of my talks is provided here as a sample. To run the sample:

    ./fix-slides.py --keynote sample/scalding-at-etsy-v2.key --notes sample/notes.txt --outdir out
	
That should create `out/out.pdf`.
