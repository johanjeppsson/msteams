import json
from collections import OrderedDict

import pytest

from msteams import DateInput, MultipleChoiceInput, TextInput

EXPECTED_INPUT = OrderedDict((
                              ("@type", "type"),
                              ("id", "comment"),
                              ("isRequired", False),
                              ("title", "Input's title property"),
                              ("value", "Input's value property"),
                              ))
EXPECTED_TEXT = OrderedDict((
                             ("isMultiline", True),
                             ("maxLength", 80),
                            ))
EXPECTED_DATE = {'includeTime': False}
EXPECTED_MULTI = OrderedDict((('choices',
                               [OrderedDict((('display', 'Choice 1'),
                                             ('value', '1')))]),
                              ('isMultiSelect', False),
                              ('style', 'normal')))


def test_text_input():

    e = EXPECTED_INPUT.copy()
    e.update(EXPECTED_TEXT)
    e['@type'] = "TextInput"

    ti = TextInput(id=e['id'], is_multiline=e['isMultiline'], title=e['title'],
                   is_required=False, value=e['value'],
                   max_length=e['maxLength'])
    assert ti.json_payload == json.dumps(e)

    ti = TextInput()
    ti.set_id(e['id'])
    ti.set_is_required(e['isRequired'])
    ti.set_is_multiline(e['isMultiline'])
    ti.set_title(e['title'])
    ti.set_value(e['value'])
    ti.set_max_length(e['maxLength'])
    assert ti.json_payload == json.dumps(e)


def test_date_input():

    e = EXPECTED_INPUT.copy()
    e.update(EXPECTED_DATE)
    e['@type'] = "DateInput"

    di = DateInput(id=e['id'], title=e['title'], is_required=False,
                   value=e['value'], include_time=e['includeTime'])
    assert di.json_payload == json.dumps(e)

    di = DateInput(id=e['id'], title=e['title'], is_required=False,
                   value=e['value'])
    di.set_include_time(e['includeTime'])
    assert di.json_payload == json.dumps(e)


def test_multiple_choice_input():

    e = EXPECTED_INPUT.copy()
    e.update(EXPECTED_MULTI)
    e['@type'] = "MultipleChoiceInput"
    c = {e['choices'][0]['display']: e['choices'][0]['value']}

    mi = MultipleChoiceInput(id=e['id'], title=e['title'], is_required=False,
                             value=e['value'], choices=c,
                             is_multi_select=False, style='normal')

    assert mi.json_payload == json.dumps(e)

    mi = MultipleChoiceInput(id=e['id'], title=e['title'], is_required=False,
                             value=e['value'])
    mi.set_choices(c)
    mi.set_is_multi_select(False)
    mi.set_style('normal')
    assert mi.json_payload == json.dumps(e)

    mi = MultipleChoiceInput(id=e['id'], title=e['title'], is_required=False,
                             value=e['value'])
    mi.add_choices(c)
    mi.set_is_multi_select(False)
    mi.set_style('normal')
    assert mi.json_payload == json.dumps(e)

    with pytest.raises(ValueError):
        mi = MultipleChoiceInput(style='invalid')
