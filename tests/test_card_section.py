import json
from collections import OrderedDict

import pytest

from msteams import CardSection, Fact, HttpPostAction, ImageObject

EXPECTED_ACTIVITY = OrderedDict((
    ("activityTitle", "John Doe"),
    ("activitySubtitle", "10/2/2019, 21:54"),
    ("activityImage", "https://tinyurl.com/y4nxy7fj"),
))
EXPECTED_FACTS = {
    "facts": [
        OrderedDict((
          ("name", "Board:"),
          ("value", "Name of board"),
        )),
        OrderedDict((
          ("name", "List:"),
          ("value", "Name of list"),
        )),
        OrderedDict((
          ("name", "Assigned to:"),
          ("value", "(none)"),
        )),
        OrderedDict((
          ("name", "Due date:"),
          ("value", "(none)"),
        )),
    ]
}
EXPECTED_TEXT = OrderedDict({"text": "Lorem ipsum dolor sit amet"})
EXPECTED_HERO = OrderedDict({"heroImage":
                             OrderedDict((("image",
                                           'https://tinyurl.com/yypszv2s'),
                                          ("title", "Everyday Hero")))
                             })
EXPECTED_TITLE = OrderedDict({"title": "Section title"})
EXPECTED_GROUP = OrderedDict({"startGroup": True})
EXPECTED_ACTION = OrderedDict({"potentialAction": [
                            OrderedDict((("@type", "HttpPOST"),
                                         ("name", "Run tests"),
                                         ("target",
                                         "http://jenkins.com?action=trigger")))
                                ]})


def test_activity():
    e = EXPECTED_ACTIVITY

    section = CardSection()
    section.set_activity(title=e['activityTitle'],
                         subtitle=e['activitySubtitle'],
                         image_url=e['activityImage'])

    assert section.json_payload == json.dumps(e)

    section = CardSection()
    section.set_activity_title(e['activityTitle'])
    section.set_activity_subtitle(e['activitySubtitle'])
    section.set_activity_image(e['activityImage'])

    assert section.json_payload == json.dumps(e)

    section = CardSection(activity_title=e['activityTitle'],
                          activity_subtitle=e['activitySubtitle'],
                          activity_image=e['activityImage'])
    assert section.json_payload == json.dumps(e)


def test_facts():
    e = EXPECTED_FACTS
    fact_dict = OrderedDict()
    for f in e['facts']:
        fact_dict[f['name']] = f['value']

    section = CardSection()
    section.set_facts(fact_dict)
    assert section.json_payload == json.dumps(e)

    section = CardSection()
    section.add_facts(fact_dict)
    assert section.json_payload == json.dumps(e)

    section = CardSection()
    for fact in e['facts']:
        section.add_fact(fact['name'], fact['value'])
    assert section.json_payload == json.dumps(e)

    section = CardSection(facts=fact_dict)
    assert section.json_payload == json.dumps(e)


def test_texts():
    e = EXPECTED_TEXT
    section = CardSection()
    section.set_text(e['text'])
    assert section.json_payload == json.dumps(e)

    section = CardSection(text=e['text'])
    assert section.json_payload == json.dumps(e)


def test_hero_image():
    e = EXPECTED_HERO
    image = ImageObject(image=e['heroImage']['image'],
                        title=e['heroImage']['title'])

    section = CardSection()
    section.set_hero_image(image)
    assert section.json_payload == json.dumps(e)

    section = CardSection()
    section.set_hero_image({e['heroImage']['title']: e['heroImage']['image']})
    assert section.json_payload == json.dumps(e)

    section = CardSection()
    section.set_hero_image(e['heroImage']['image'])
    section['hero_image'].set_title(e['heroImage']['title'])
    assert section.json_payload == json.dumps(e)

    section = CardSection(hero_image={e['heroImage']['title']:
                                      e['heroImage']['image']})
    assert section.json_payload == json.dumps(e)


def test_title():
    e = EXPECTED_TITLE

    section = CardSection()
    section.set_title(e['title'])
    assert section.json_payload == json.dumps(e)

    section = CardSection(title=e['title'])
    assert section.json_payload == json.dumps(e)


def test_start_group():
    e = EXPECTED_TITLE
    e.update(EXPECTED_GROUP)

    section = CardSection()
    section.set_title(e['title'])
    section.start_group()
    assert section.json_payload == json.dumps(e)


def test_potential_actions():
    e = EXPECTED_ACTION

    section = CardSection()
    with pytest.raises(TypeError):
        section.add_potential_action(Fact('a', 'b'))
    action = HttpPostAction(name=e['potentialAction'][0]['name'],
                            target=e['potentialAction'][0]['target'])
    section.add_potential_action(action)
    assert section.json_payload == json.dumps(e)


def test_total():
    e = EXPECTED_ACTIVITY
    e.update(EXPECTED_TITLE)
    e.update(EXPECTED_FACTS)
    e.update(EXPECTED_TEXT)
    e.update(EXPECTED_HERO)

    section = CardSection()
    section = CardSection(title=e['title'])
    section.set_activity(title=e['activityTitle'],
                         subtitle=e['activitySubtitle'],
                         image_url=e['activityImage'])
    for fact in e['facts']:
        section.add_fact(fact['name'], fact['value'])

    section.set_text(e['text'])
    section.set_hero_image({e['heroImage']['title']: e['heroImage']['image']})

    section.json_payload == json.dumps(e)
