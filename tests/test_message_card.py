import json
from collections import OrderedDict

import pytest

from msteams import CardSection, HttpPostAction, MessageCard

EXP_TITLE = OrderedDict({"title": "Card Title"})
EXP_SUMMARY = OrderedDict({"summary": "Card summary"})
EXP_TEXT = OrderedDict({"text": "Lorem ipsum dolor sit amet"})
EXP_COLOR = OrderedDict({"themeColor": "FF5500"})

EXP_SECTIONS = {"sections": [{"title": "Section title"}]}
EXP_ACTION = {
    "potentialAction": [
        OrderedDict(
            (
                ("@type", "HttpPOST"),
                ("name", "Run tests"),
                ("target", "http://jenkins.com?action=trigger"),
            )
        )
    ]
}


def _get_exp_card():
    """Return expected basic result for MessageCard."""
    return OrderedDict(
        (
            ("@type", "MessageCard"),
            ("@context", "https://schema.org/extensions"),
            ("summary", "Summary"),
        )
    )


def test_message_card():
    e = _get_exp_card()

    e.update(EXP_SUMMARY)
    card = MessageCard(summary=e["summary"])
    assert card.json_payload == json.dumps(e)

    card = MessageCard()
    card.set_summary(e["summary"])
    assert card.json_payload == json.dumps(e)

    e.update(EXP_TITLE)
    card = MessageCard(summary=e["summary"], title=e["title"])
    assert card.json_payload == json.dumps(e)

    card = MessageCard(summary=e["summary"])
    card.set_title(e["title"])
    assert card.json_payload == json.dumps(e)

    e.update(EXP_TEXT)
    card = MessageCard(summary=e["summary"], title=e["title"], text=e["text"])
    assert card.json_payload == json.dumps(e)

    card = MessageCard(summary=e["summary"], title=e["title"])
    card.set_text(e["text"])
    assert card.json_payload == json.dumps(e)

    e.update(EXP_COLOR)
    card = MessageCard(
        summary=e["summary"],
        title=e["title"],
        text=e["text"],
        theme_color=e["themeColor"],
    )
    assert card.json_payload == json.dumps(e)
    card = MessageCard(summary=e["summary"], title=e["title"], text=e["text"])
    card.set_theme_color(e["themeColor"])
    assert card.json_payload == json.dumps(e)


def test_sections():
    e = _get_exp_card()
    e.update(EXP_SECTIONS)

    card = MessageCard()
    s = CardSection(title=EXP_SECTIONS["sections"][0]["title"])
    card.set_sections(s)
    assert card.json_payload == json.dumps(e)

    card = MessageCard()
    card.add_section(s)
    assert card.json_payload == json.dumps(e)

    card = MessageCard(sections=s)
    assert card.json_payload == json.dumps(e)


def test_actions():
    e = _get_exp_card()
    e.update(EXP_ACTION)
    a = HttpPostAction(
        name=e["potentialAction"][0]["name"], target=e["potentialAction"][0]["target"]
    )

    card = MessageCard(potential_action=[a])
    assert card.json_payload == json.dumps(e)

    card = MessageCard()
    card.add_potential_action(a)
    assert card.json_payload == json.dumps(e)

    card = MessageCard()
    card.set_potential_actions([a])
    assert card.json_payload == json.dumps(e)
