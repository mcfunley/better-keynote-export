import os

from keynote_export.export import Options, generate_html


def slide(outdir, n, note="a note", width=1920, height=1080):
    return {
        "variants": [
            (os.path.join(outdir, "slides", "slides.%03d-%d.webp" % (n, w)), w)
            for w in (480, 960, 1440, width)
        ],
        "width": width,
        "height": height,
        "note": note,
    }


def render(tmp_path, bsky_handle=None, mastodon_handle=None, slides=()):
    opts = Options(
        outdir=str(tmp_path),
        pagesize=(1920, 1080),
        font_size=36,
        title="A Talk",
        bsky_handle=bsky_handle,
        mastodon_handle=mastodon_handle,
        skip_builds=False,
    )
    generate_html(opts, list(slides))
    return open(os.path.join(opts.outdir, "index.html")).read()


def test_no_handles_omits_share(tmp_path):
    html = render(tmp_path)
    assert 'class="share"' not in html
    assert "@None" not in html


def test_bsky_handle_only(tmp_path):
    html = render(tmp_path, bsky_handle="mcfunley.com")
    assert "https://bsky.app/profile/mcfunley.com" in html
    assert "@mcfunley.com" in html
    assert "mastodon.social" not in html


def test_mastodon_handle_only(tmp_path):
    html = render(tmp_path, mastodon_handle="mcfunley")
    assert "https://mastodon.social/@mcfunley" in html
    assert "@mcfunley" in html
    assert "bsky.app" not in html


def test_both_handles(tmp_path):
    html = render(tmp_path, bsky_handle="mcfunley.com", mastodon_handle="mcfunley")
    assert "https://bsky.app/profile/mcfunley.com" in html
    assert "https://mastodon.social/@mcfunley" in html


def test_slide_paths_are_relative_to_the_outdir(tmp_path):
    html = render(tmp_path, slides=[slide(str(tmp_path), 1)])
    assert str(tmp_path) not in html
    assert 'src="slides/slides.001-1920.webp"' in html


def test_srcset_lists_every_variant(tmp_path):
    html = render(tmp_path, slides=[slide(str(tmp_path), 1)])
    assert (
        'srcset="slides/slides.001-480.webp 480w, '
        "slides/slides.001-960.webp 960w, "
        "slides/slides.001-1440.webp 1440w, "
        'slides/slides.001-1920.webp 1920w"'
    ) in html


def test_src_falls_back_to_the_widest_variant(tmp_path):
    html = render(tmp_path, slides=[slide(str(tmp_path), 1, width=800)])
    assert 'src="slides/slides.001-800.webp"' in html


def test_sizes_matches_the_stylesheet_breakpoint(tmp_path):
    html = render(tmp_path, slides=[slide(str(tmp_path), 1)])
    assert (
        'sizes="(max-width: 820px) calc(100vw - 40px), '
        "(max-width: 1920px) calc((100vw - 168px) * 0.592), "
        '1037px"'
    ) in html


def test_slides_keep_their_numeric_anchors(tmp_path):
    """Deep links to published talks point at #1, #2, ... so the ids are load-bearing."""
    html = render(
        tmp_path, slides=[slide(str(tmp_path), n) for n in range(1, 4)]
    )
    for n in (1, 2, 3):
        assert 'id="%d"' % n in html
        assert 'href="#%d"' % n in html


def test_intrinsic_dimensions_are_emitted(tmp_path):
    html = render(tmp_path, slides=[slide(str(tmp_path), 1)])
    assert 'width="1920"' in html
    assert 'height="1080"' in html


def test_only_the_first_slide_loads_eagerly(tmp_path):
    html = render(
        tmp_path, slides=[slide(str(tmp_path), n) for n in range(1, 4)]
    )
    assert html.count('loading="eager"') == 1
    assert html.count('loading="lazy"') == 2


def test_note_lines_become_paragraphs(tmp_path):
    html = render(tmp_path, slides=[slide(str(tmp_path), 1, note="one\ntwo")])
    assert "<p>one</p><p>two</p>" in html
    assert "<br />" not in html


def test_blank_lines_do_not_make_empty_paragraphs(tmp_path):
    html = render(
        tmp_path, slides=[slide(str(tmp_path), 1, note="one\n\n\ntwo")]
    )
    assert "<p>one</p><p>two</p>" in html
    assert "<p></p>" not in html


def test_a_note_with_no_text_renders_no_paragraphs(tmp_path):
    html = render(tmp_path, slides=[slide(str(tmp_path), 1, note="")])
    assert "<p>" not in html.split('class="slide-note"')[1].split("</div>")[0]


def test_no_jpegs_are_referenced(tmp_path):
    html = render(
        tmp_path, slides=[slide(str(tmp_path), n) for n in range(1, 4)]
    )
    assert ".jpeg" not in html
