# keynote-export

* It generates an html presentation in a [minimalist, reader-friendly format](https://boringtechnology.club).
* It generates a nicely-formatted PDF [like this one](https://speakerdeck.com/mcfunley/deploying-often-is-a-very-good-idea), suitable for uploading to Speakerdeck or others.

## Setup
You can install this program using [pipx](https://github.com/pypa/pipx):

    pipx install keynote-export

## Usage

Use `keynote-export --help` to see all of the available options. Basically,

```
keynote-export \
  --keynote=<the keynote file> \
  --outdir=<a path> \
  --title=<the name of the presentation> \
  --bluesky-handle=<your BlueSky username>
```
