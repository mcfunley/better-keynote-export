import os

import pytest
from PIL import Image

from keynote_export.export import (
    SHARE_IMAGE,
    SHARE_IMAGE_WIDTH,
    Options,
    generate_html,
    generate_share_image,
)


def make_slides(slidesdir, count=2, size=(1920, 1080)):
    os.makedirs(slidesdir, exist_ok=True)
    for i in range(1, count + 1):
        Image.new("RGB", size, (i * 40 % 256, 90, 140)).save(
            os.path.join(slidesdir, "slides.%03d.jpeg" % i)
        )


def opts_for(tmp_path, **kw):
    kw.setdefault("title", "A Talk")
    return Options(
        outdir=str(tmp_path),
        pagesize=(1920, 1080),
        font_size=36,
        bsky_handle=None,
        mastodon_handle=None,
        skip_builds=False,
        **kw
    )


def render(tmp_path, share=None, **kw):
    opts = opts_for(tmp_path, **kw)
    generate_html(opts, [], False, share)
    return open(os.path.join(opts.outdir, "index.html")).read()


SHARE = {"name": SHARE_IMAGE, "width": 1200, "height": 675}


# ---- the share image ----------------------------------------------------


def test_share_image_defaults_to_the_first_slide(tmp_path):
    opts = opts_for(tmp_path)
    make_slides(opts.slidesdir, count=3)

    share = generate_share_image(opts)

    assert share["name"] == SHARE_IMAGE
    first = Image.open(os.path.join(opts.slidesdir, "slides.001.jpeg"))
    with Image.open(os.path.join(str(tmp_path), SHARE_IMAGE)) as written:
        assert written.getpixel((5, 5)) == pytest.approx(first.getpixel((5, 5)), abs=8)


def test_share_image_is_scaled_and_keeps_aspect(tmp_path):
    opts = opts_for(tmp_path)
    make_slides(opts.slidesdir)

    share = generate_share_image(opts)

    assert share["width"] == SHARE_IMAGE_WIDTH
    assert share["height"] == round(SHARE_IMAGE_WIDTH * 1080 / 1920)
    with Image.open(os.path.join(str(tmp_path), SHARE_IMAGE)) as im:
        assert im.size == (share["width"], share["height"])
        assert im.format == "JPEG"


def test_share_image_can_be_overridden(tmp_path):
    override = os.path.join(str(tmp_path), "custom.png")
    Image.new("RGB", (800, 400), (10, 200, 10)).save(override)

    opts = opts_for(tmp_path, share_image=override)
    make_slides(opts.slidesdir)

    share = generate_share_image(opts)

    assert share["width"] == 800
    assert share["height"] == 400
    with Image.open(os.path.join(str(tmp_path), SHARE_IMAGE)) as im:
        assert im.getpixel((400, 200))[1] > 150


def test_share_image_is_not_upscaled(tmp_path):
    override = os.path.join(str(tmp_path), "small.png")
    Image.new("RGB", (300, 169)).save(override)

    share = generate_share_image(opts_for(tmp_path, share_image=override))

    assert share["width"] == 300


def test_no_slides_and_no_override_writes_nothing(tmp_path):
    opts = opts_for(tmp_path)
    os.makedirs(opts.slidesdir, exist_ok=True)

    assert generate_share_image(opts) is None
    assert not os.path.exists(os.path.join(str(tmp_path), SHARE_IMAGE))


# ---- the tags -----------------------------------------------------------


def test_open_graph_uses_property_not_name(tmp_path):
    """og:* is RDFa. Scrapers look for property=, and ignore name=."""
    html = render(tmp_path, share=SHARE, url="https://example.com", description="Hi")

    for tag in ("og:title", "og:url", "og:image", "og:description", "og:type"):
        assert 'property="%s"' % tag in html
        assert 'name="%s"' % tag not in html


def test_description_lands_in_both_places(tmp_path):
    html = render(tmp_path, description="How to be old, for young people.")
    assert '<meta name="description" content="How to be old, for young people.">' in html
    assert (
        '<meta property="og:description" content="How to be old, for young people.">'
        in html
    )


def test_urls_are_absolute(tmp_path):
    html = render(tmp_path, share=SHARE, url="https://evaluation.club")
    assert '<meta property="og:url" content="https://evaluation.club">' in html
    assert (
        '<meta property="og:image" content="https://evaluation.club/share.jpg">' in html
    )


def test_trailing_slash_does_not_double_up(tmp_path):
    html = render(tmp_path, share=SHARE, url="https://evaluation.club/")
    assert "https://evaluation.club/share.jpg" in html
    assert "//share.jpg" not in html


def test_canonical_link(tmp_path):
    html = render(tmp_path, url="https://evaluation.club")
    assert '<link rel="canonical" href="https://evaluation.club">' in html


def test_image_dimensions_are_published(tmp_path):
    html = render(tmp_path, share=SHARE, url="https://example.com")
    assert '<meta property="og:image:width" content="1200">' in html
    assert '<meta property="og:image:height" content="675">' in html


def test_image_tags_need_an_absolute_base(tmp_path):
    """Relative og:image is invalid, so without --url it is left out."""
    html = render(tmp_path, share=SHARE)
    assert "og:image" not in html
    assert "og:url" not in html
    assert "canonical" not in html


def test_title_is_always_advertised(tmp_path):
    html = render(tmp_path)
    assert '<meta property="og:title" content="A Talk">' in html
    assert '<meta property="og:type" content="website">' in html


def test_twitter_card_reflects_whether_there_is_an_image(tmp_path):
    with_image = render(tmp_path, share=SHARE, url="https://example.com")
    assert '<meta name="twitter:card" content="summary_large_image">' in with_image

    without = render(tmp_path)
    assert '<meta name="twitter:card" content="summary">' in without


def test_quotes_in_metadata_are_escaped(tmp_path):
    html = render(
        tmp_path, title='The "Real" Talk', description='He said "no" to it'
    )
    assert '&#34;Real&#34;' in html or "&quot;Real&quot;" in html
    assert 'content="The "Real" Talk"' not in html
