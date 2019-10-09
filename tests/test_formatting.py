import pytest

from msteams.formatting import (
    bold,
    header,
    italic,
    ordered_list,
    strikethrough,
    unordered_list,
    preformatted,
    blockquote,
    link,
    img,
)


def test_bold():

    assert bold("text") == "<strong>text</strong>"


def test_italic():

    assert italic("text") == "<em>text</em>"


def test_header():

    assert header("text") == "<h1>text</h1>"
    assert header("text", level=2) == "<h2>text</h2>"
    assert header("text", level=3) == "<h3>text</h3>"

    with pytest.raises(ValueError):
        header("text", level=4)


def test_strikethrough():

    assert strikethrough("text") == "<strike>text</strike>"


def test_unordered_list():

    assert unordered_list(["text", "more"]) == "<ul><li>text</li><li>more</li></ul>"


def test_ordered_list():

    assert ordered_list(["text", "more"]) == "<ol><li>text</li><li>more</li></ol>"


def test_preformatted():

    assert preformatted("text") == "<pre>text</pre>"


def test_blockquote():

    assert blockquote("text") == "<blockquote>text</blockquote>"


def test_link():

    assert (
        link("Python", "http://www.python.org")
        == '<a href="http://www.python.org">Python</a>'
    )


def test_img():

    assert (
        img("http://aka.ms/Fo983c", "Duck on a rock")
        == '<img src="http://aka.ms/Fo983c" alt="Duck on a rock"></img>'
    )
    assert img("http://aka.ms/Fo983c") == '<img src="http://aka.ms/Fo983c"></img>'
