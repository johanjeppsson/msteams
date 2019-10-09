"""Convenience formatting functions for MessageCards.'

Uses the HTML formatting as described here:
https://docs.microsoft.com/en-us/microsoftteams/platform/concepts/cards/cards-format#html-formatting-for-connector-cards
"""


def _tag(s, tag):
    """Return string wrapped in a tag."""
    return "<{0}>{1}</{0}>".format(tag, s)


def bold(s):
    """Return bold string."""
    return _tag(s, "strong")


def italic(s):
    """Return italicized string."""
    return _tag(s, "em")


def header(s, level=1):
    """Return header. Valid levels are 1-3."""
    if level < 1 or level > 3:
        raise ValueError("Level must be in range 1-3")
    return _tag(s, "h{}".format(level))


def strikethrough(s):
    """Return strikethrough stirng."""
    return _tag(s, "strike")


def unordered_list(l):
    """Return string representing an unordered list."""
    return _tag("".join([_tag(s, "li") for s in l]), "ul")


def ordered_list(l):
    """Return string representing an ordered list."""
    return _tag("".join([_tag(s, "li") for s in l]), "ol")


def preformatted(s):
    """Return preformatted text."""
    return _tag(s, "pre")


def blockquote(s):
    """Return blockquote text."""
    return _tag(s, "blockquote")


def link(text, url):
    """Return formatted hyperlink."""
    return '<a href="{}">{}</a>'.format(url, text)


def img(url, alt_text=None):
    """Return formatted embedded image."""
    alt = ' alt="{}"'.format(alt_text) if alt_text is not None else ""
    return '<img src="{}"{}></img>'.format(url, alt)
