import os

from keynote_export.export import Options, generate_html


def render(tmp_path, bsky_handle=None, mastodon_handle=None):
    opts = Options(
        outdir=str(tmp_path),
        pagesize=(1920, 1080),
        font_size=36,
        title="A Talk",
        bsky_handle=bsky_handle,
        mastodon_handle=mastodon_handle,
        skip_builds=False,
    )
    generate_html(opts, [])
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
