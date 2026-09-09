import os

import pytest
from click.testing import CliRunner

from keynote_export.export import Options, generate_html, main, render_markdown


def write(tmp_path, name, text):
    p = os.path.join(str(tmp_path), name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def render(
    tmp_path, abstract=None, footer=None, header_link_url=None, header_link_text=None
):
    opts = Options(
        outdir=str(tmp_path),
        pagesize=(1920, 1080),
        font_size=36,
        title="A Talk",
        bsky_handle=None,
        mastodon_handle=None,
        skip_builds=False,
        abstract=abstract,
        footer=footer,
        header_link_url=header_link_url,
        header_link_text=header_link_text,
    )
    generate_html(opts, [])
    return open(os.path.join(opts.outdir, "index.html")).read()


def test_render_markdown_returns_none_without_a_path():
    assert render_markdown(None) is None
    assert render_markdown("") is None


def test_render_markdown_converts_a_file(tmp_path):
    p = write(tmp_path, "a.md", "A talk about *agents*.")
    assert render_markdown(p) == "<p>A talk about <em>agents</em>.</p>"


def test_render_markdown_handles_lists_and_links(tmp_path):
    p = write(tmp_path, "a.md", "- one\n- [two](https://example.com)\n")
    html = render_markdown(p)
    assert "<ul>" in html
    assert '<a href="https://example.com">two</a>' in html


def test_abstract_is_rendered_in_the_header(tmp_path):
    html = render(tmp_path, abstract="<p>The abstract.</p>")
    assert "<p>The abstract.</p>" in html
    assert 'class="prose"' in html


def test_footer_is_rendered_above_the_colophon(tmp_path):
    html = render(tmp_path, footer="<p>Talk given somewhere.</p>")
    assert "<p>Talk given somewhere.</p>" in html
    assert html.index("Talk given somewhere") < html.index("Generated with")


def test_the_keynote_export_credit_survives_a_custom_footer(tmp_path):
    html = render(tmp_path, footer="<p>Mine.</p>")
    assert "better-keynote-export" in html
    assert 'class="colophon"' in html


def test_no_abstract_emits_no_placeholder(tmp_path):
    html = render(tmp_path)
    assert "Edit this to add an abstract" not in html
    assert "<header>" in html


def test_no_footer_still_renders_the_credit(tmp_path):
    html = render(tmp_path)
    assert "better-keynote-export" in html


def test_markdown_html_is_not_escaped(tmp_path):
    html = render(tmp_path, abstract="<p>A <em>talk</em>.</p>")
    assert "<em>talk</em>" in html
    assert "&lt;em&gt;" not in html


@pytest.mark.parametrize("region", ["abstract", "footer"])
def test_each_region_is_independent(tmp_path, region):
    html = render(tmp_path, **{region: "<p>Only this one.</p>"})
    assert html.count("Only this one.") == 1


def test_header_link_is_rendered(tmp_path):
    html = render(
        tmp_path,
        header_link_url="https://dotclub.club",
        header_link_text="The .club Club",
    )
    assert '<a href="https://dotclub.club">The .club Club</a>' in html
    assert 'class="header-link"' in html


def test_header_link_sits_above_the_title(tmp_path):
    html = render(
        tmp_path, header_link_url="https://example.com", header_link_text="Elsewhere"
    )
    assert html.index("Elsewhere") < html.index("<h1>")


def test_no_header_link_emits_nothing(tmp_path):
    html = render(tmp_path)
    assert "header-link" not in html
    assert "<nav" not in html


@pytest.mark.parametrize(
    "args",
    [
        ["--header-link", "https://example.com"],
        ["--header-link-text", "Elsewhere"],
    ],
)
def test_half_a_header_link_is_a_usage_error(tmp_path, args):
    """Checked before any Keynote work, so this never opens the deck."""
    deck = write(tmp_path, "deck.key", "")
    result = CliRunner().invoke(
        main,
        ["--keynote", deck, "--outdir", str(tmp_path), "--title", "A Talk"] + args,
    )
    assert result.exit_code != 0
    assert "go together" in result.output
