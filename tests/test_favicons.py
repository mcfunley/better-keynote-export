import json
import os

import pytest
from PIL import Image

from keynote_export.export import (
    APPLE_TOUCH_SIZE,
    ICO_SIZES,
    MANIFEST_ICON_SIZES,
    Options,
    favicon_master,
    favicon_variant,
    generate_favicons,
    generate_html,
)

# A red square with a transparent margin, so a background shows through.
SVG = """<?xml version="1.0" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"
     viewBox="0 0 100 100">
  <rect x="20" y="20" width="60" height="60" fill="#ff0000"/>
</svg>
"""


def write_svg(tmp_path, name="icon.svg", body=SVG):
    p = os.path.join(str(tmp_path), name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    return p


def opts_for(tmp_path, favicon=None):
    return Options(
        outdir=str(tmp_path),
        pagesize=(1920, 1080),
        font_size=36,
        title="A Talk",
        bsky_handle=None,
        mastodon_handle=None,
        skip_builds=False,
        favicon=favicon,
    )


def test_no_favicon_writes_nothing(tmp_path):
    assert generate_favicons(opts_for(tmp_path)) is False
    assert os.listdir(str(tmp_path)) == []


def test_generates_the_whole_set(tmp_path):
    svg = write_svg(tmp_path)
    assert generate_favicons(opts_for(tmp_path, svg)) is True

    expected = ["favicon.svg", "favicon.ico", "apple-touch-icon.png", "site.webmanifest"]
    expected += ["icon-%d.png" % s for s in MANIFEST_ICON_SIZES]
    for name in expected:
        assert os.path.exists(os.path.join(str(tmp_path), name)), name


def test_svg_is_copied_verbatim(tmp_path):
    svg = write_svg(tmp_path)
    generate_favicons(opts_for(tmp_path, svg))
    with open(os.path.join(str(tmp_path), "favicon.svg"), encoding="utf-8") as f:
        assert f.read() == SVG


def test_png_derivatives_are_the_right_size(tmp_path):
    svg = write_svg(tmp_path)
    generate_favicons(opts_for(tmp_path, svg))

    with Image.open(os.path.join(str(tmp_path), "apple-touch-icon.png")) as im:
        assert im.size == (APPLE_TOUCH_SIZE, APPLE_TOUCH_SIZE)

    for size in MANIFEST_ICON_SIZES:
        with Image.open(os.path.join(str(tmp_path), "icon-%d.png" % size)) as im:
            assert im.size == (size, size)


def test_ico_carries_every_size(tmp_path):
    svg = write_svg(tmp_path)
    generate_favicons(opts_for(tmp_path, svg))
    with Image.open(os.path.join(str(tmp_path), "favicon.ico")) as im:
        assert {s for s, _ in im.info["sizes"]} >= set(ICO_SIZES)


def test_apple_touch_icon_is_opaque(tmp_path):
    """iOS composites transparency onto black, so this one cannot have any."""
    svg = write_svg(tmp_path)
    generate_favicons(opts_for(tmp_path, svg))
    with Image.open(os.path.join(str(tmp_path), "apple-touch-icon.png")) as im:
        assert im.mode == "RGB"
        assert im.convert("RGBA").getchannel("A").getextrema() == (255, 255)


def test_manifest_lists_the_icons(tmp_path):
    svg = write_svg(tmp_path)
    generate_favicons(opts_for(tmp_path, svg))
    with open(os.path.join(str(tmp_path), "site.webmanifest"), encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["name"] == "A Talk"
    assert [i["src"] for i in manifest["icons"]] == [
        "icon-%d.png" % s for s in MANIFEST_ICON_SIZES
    ]
    for icon in manifest["icons"]:
        assert os.path.exists(os.path.join(str(tmp_path), icon["src"]))


def test_variant_without_a_background_keeps_transparency(tmp_path):
    master = favicon_master(write_svg(tmp_path))
    art = favicon_variant(master, 64)
    assert art.size == (64, 64)
    assert art.getchannel("A").getextrema()[0] == 0


def test_variant_with_a_background_fills_the_corners(tmp_path):
    master = favicon_master(write_svg(tmp_path))
    art = favicon_variant(master, 64, "#ffffff")
    assert art.getpixel((0, 0))[3] == 255


@pytest.mark.parametrize("present", [True, False])
def test_html_links_only_when_icons_exist(tmp_path, present):
    generate_html(opts_for(tmp_path), [], present)
    html = open(os.path.join(str(tmp_path), "index.html")).read()

    for tag in ['rel="icon"', 'rel="apple-touch-icon"', 'rel="manifest"']:
        assert (tag in html) is present


def test_html_links_both_icon_formats(tmp_path):
    generate_html(opts_for(tmp_path), [], True)
    html = open(os.path.join(str(tmp_path), "index.html")).read()
    assert '<link rel="icon" href="favicon.ico" sizes="32x32">' in html
    assert '<link rel="icon" href="favicon.svg" type="image/svg+xml">' in html
