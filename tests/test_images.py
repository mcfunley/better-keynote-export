import os

import pytest
from PIL import Image

from keynote_export.export import (
    Options,
    generate_images,
    srcset,
    variant_widths,
)


def make_slides(slidesdir, count, size=(1920, 1080)):
    os.makedirs(slidesdir, exist_ok=True)
    for i in range(1, count + 1):
        img = Image.new("RGB", size, (i * 10 % 256, 100, 150))
        img.save(os.path.join(slidesdir, "slides.%03d.jpeg" % i))


@pytest.fixture
def opts(tmp_path):
    o = Options(
        outdir=str(tmp_path),
        pagesize=(1920, 1080),
        font_size=36,
        title="A Talk",
        bsky_handle=None,
        mastodon_handle=None,
        skip_builds=False,
    )
    return o


def test_variant_widths_stops_at_native():
    assert variant_widths(1920) == [480, 960, 1440, 1920]


def test_variant_widths_never_upscales():
    assert variant_widths(1000) == [480, 960, 1000]


def test_variant_widths_no_duplicate_at_boundary():
    widths = variant_widths(960)
    assert widths == [480, 960]
    assert len(widths) == len(set(widths))


def test_variant_widths_narrower_than_smallest():
    assert variant_widths(320) == [320]


def test_srcset_formats_width_descriptors():
    assert srcset([("a-480.webp", 480), ("a-960.webp", 960)]) == (
        "a-480.webp 480w, a-960.webp 960w"
    )


def test_generate_images_writes_a_webp_per_width(opts):
    make_slides(opts.slidesdir, 2)

    slides = generate_images(opts, ["one", "two"])

    assert len(slides) == 2
    for slide in slides:
        assert [w for _, w in slide["variants"]] == [480, 960, 1440, 1920]
        for path, _ in slide["variants"]:
            assert os.path.exists(path)


def test_generate_images_scales_to_each_width(opts):
    make_slides(opts.slidesdir, 1)

    slides = generate_images(opts, ["note"])

    for path, w in slides[0]["variants"]:
        with Image.open(path) as img:
            assert img.format == "WEBP"
            assert img.width == w
            # 16:9 preserved.
            assert img.height == round(w * 1080 / 1920)


def test_generate_images_reports_native_size(opts):
    make_slides(opts.slidesdir, 1)

    slides = generate_images(opts, ["note"])

    assert slides[0]["width"] == 1920
    assert slides[0]["height"] == 1080


def test_generate_images_keeps_notes_with_slides(opts):
    make_slides(opts.slidesdir, 3)

    slides = generate_images(opts, ["one", "two", "three"])

    assert [s["note"] for s in slides] == ["one", "two", "three"]


def test_generate_images_removes_the_jpeg_originals(opts):
    make_slides(opts.slidesdir, 2)

    generate_images(opts, ["one", "two"])

    assert [f for f in os.listdir(opts.slidesdir) if f.endswith(".jpeg")] == []


def test_generate_images_does_not_upscale_a_small_deck(opts):
    make_slides(opts.slidesdir, 1, size=(800, 450))

    slides = generate_images(opts, ["note"])

    assert [w for _, w in slides[0]["variants"]] == [480, 800]
