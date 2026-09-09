# keynote-export

This is a program that can export Keynote presentations in formats that are better for sharing them.

* It generates an html presentation in a [minimalist, reader-friendly format](https://boringtechnology.club).
* It generates a nicely-formatted PDF [like this one](https://speakerdeck.com/mcfunley/deploying-often-is-a-very-good-idea), suitable for uploading to Speakerdeck or others.

Natively,

* Keynote will export slides with presenter notes as a PDF. But the resulting formatting is terrible, giving 50% of each page of the PDF up to the notes.
* Keynote will export an HTML document, but it won't include presenter notes with it.

This program addresses both of these issues.

## Setup
You can install this program using [pipx](https://github.com/pypa/pipx):

    pipx install keynote-export

## Examples and Screenshots

[Here is an example of the HTML site generated](http://pushtrain.club).

You also get PDF presentation slides that look like this:

![A nice looking slide](/img/nice-slide.png?raw=true)

Instead of the crappy ones that Keynote gives you:

![A horrible looking slide](/img/bad-slide.png?raw=true)

A full PDF sample can be found [here](https://speakerdeck.com/mcfunley/the-push-train).

## Usage

Use `keynote-export --help` to see all of the available options. Basically,

```
keynote-export \
  --keynote=<the keynote file> \
  --outdir=<a path> \
  --title=<the name of the presentation> \
  --bluesky-handle=<your BlueSky username> \
  --mastodon-handle=<your Mastodon username>
```

The output path gets both a PDF file and a self-contained website that you can easily host with (for example) [GitHub pages](https://pages.github.com/).

There are optional flags for the parts of the page that aren't slides:

```
  --abstract=<a markdown file>   rendered under the title
  --footer=<a markdown file>     rendered in the footer
  --favicon=<an svg>             derives favicon.ico, apple-touch-icon.png and
                                 the manifest icons, and links them
  --header-link=<a url>          a small link above the title, with
  --header-link-text=<a label>   its label
```

The markdown files are read on every run, so they are where that copy should
live — the generated `index.html` gets overwritten each time.

## Notes

You must have Keynote installed to use this.

`--favicon` rasterizes the SVG with [librsvg](https://wiki.gnome.org/Projects/LibRsvg)
(`brew install librsvg`) when it is installed, and falls back to Quick Look,
which ships with macOS but flattens transparency onto white. Scale and crop the
SVG how you want it first; the derivatives are straight resamples of it.

Fundamentally, this works by scripting Keynote using Applescript. The details of this helpfully change from Keynote version to version. So if the script isn't working, it might be that I haven't updated it recently and minor tweaks are needed for the latest version of Keynote. Pull requests welcome!
