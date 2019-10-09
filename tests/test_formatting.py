import pytest

from msteams import MessageCard, CardSection
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
    paragraph,
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


def test_all():
    """Replicate example from 
    https://docs.microsoft.com/en-us/microsoftteams/platform/concepts/cards/cards-format#formatting-sample-for-html-connector-cards
    """

    card = MessageCard(summary="Summary", title="Connector Card HTML formatting")
    sections = []
    sections.append(CardSection(text=" ".join(("This is some", bold("bold"), "text"))))
    sections.append(
        CardSection(text=" ".join(("This is some", italic("italic"), "text")))
    )
    sections.append(
        CardSection(
            text=" ".join(("This is some", strikethrough("strikethrough"), "text"))
        )
    )
    sections.append(
        CardSection(
            text="\r".join(
                (
                    header("Header 1", level=1),
                    header("Header 2", level=2),
                    header("Header 3", level=3),
                )
            )
        )
    )
    sections.append(CardSection(text="bullet list " + unordered_list(["text", "text"])))
    sections.append(CardSection(text="ordered list " + ordered_list(["text", "text"])))
    sections.append(
        CardSection(text="hyperlink " + link("Bing", "https://www.bing.com/"))
    )
    sections.append(
        CardSection(
            text="embedded image " + img("http://aka.ms/Fo983c", "Duck on a rock")
        )
    )
    sections.append(CardSection(text="preformatted text " + preformatted("text")))
    sections.append(
        CardSection(text="Paragraphs " + paragraph("Line a") + paragraph("Line b"))
    )
    sections.append(CardSection(text=blockquote("Blockquote text")))

    card.set_sections(sections)

    assert (
        card.get_payload("json", indent=4)
        == """{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "summary": "Summary",
    "title": "Connector Card HTML formatting",
    "sections": [
        {
            "text": "This is some <strong>bold</strong> text"
        },
        {
            "text": "This is some <em>italic</em> text"
        },
        {
            "text": "This is some <strike>strikethrough</strike> text"
        },
        {
            "text": "<h1>Header 1</h1>\\r<h2>Header 2</h2>\\r<h3>Header 3</h3>"
        },
        {
            "text": "bullet list <ul><li>text</li><li>text</li></ul>"
        },
        {
            "text": "ordered list <ol><li>text</li><li>text</li></ol>"
        },
        {
            "text": "hyperlink <a href=\\"https://www.bing.com/\\">Bing</a>"
        },
        {
            "text": "embedded image <img src=\\"http://aka.ms/Fo983c\\" alt=\\"Duck on a rock\\"></img>"
        },
        {
            "text": "preformatted text <pre>text</pre>"
        },
        {
            "text": "Paragraphs <p>Line a</p><p>Line b</p>"
        },
        {
            "text": "<blockquote>Blockquote text</blockquote>"
        }
    ]
}"""
    )
