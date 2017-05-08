## better-keynote-export

This is a script that can export Keynote presentations in formats that are better for sharing them as standalone documents. Natively,

* Keynote will export slides with presenter notes as a PDF. But the resulting formatting is terrible, giving 50% of each page of the PDF up to the notes.
* Keynote will export an HTML document, but it won't include presenter notes with it.

This script addresses both of these issues.

* It generates a nicely-formatted PDF [like this one](https://speakerdeck.com/mcfunley/deploying-often-is-a-very-good-idea), suitable for uploading to Speakerdeck or others.
* It generates an html presentation in a minimalist, reader-friendly format inspired by [Maciej Cegłowski](http://idlewords.com/talks/).

### Examples and Screenshots

[Here is an example of the HTML site generated](http://pushtrain.club).

You also get PDF presentation slides that look like this:

![A nice looking slide](/img/nice-slide.png?raw=true)

Instead of the crappy ones that Keynote gives you:

![A horrible looking slide](/img/bad-slide.png?raw=true)

A full PDF sample can be found [here](https://speakerdeck.com/mcfunley/the-push-train).

### Setup

[pyenv virtualenv](https://github.com/pyenv/pyenv-virtualenv) is a reasonable way to have isolated python environments. Follow their instructions for setting that up and then do this:

```
$ pyenv virtualenv 3.6.1 better-keynote-export
$ pyenv activate better-keynote-export
$ pip install -r requirements.txt
```

### Usage

Use `./export.py --help` to see all of the available options. Basically,

```
./export.py \
  --keynote=<the keynote file> \
  --outdir=<a path> \
  --title=<the name of the presentation> \
  --twitter-username=<your twitter username>
```

The output path gets both a PDF file and a self-contained website that you can easily host with (for example) [GitHub pages](https://pages.github.com/).

### Notes

You must have Keynote installed to use this.

Fundamentally, this works by scripting Keynote using Applescript. The details of this helpfully change from Keynote version to version. So if the script isn't working, it might be that I haven't updated it recently and minor tweaks are needed for the latest version of Keynote. Pull requests welcome!
