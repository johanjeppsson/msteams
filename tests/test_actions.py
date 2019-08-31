import json
from collections import OrderedDict

import pytest

from msteams import HttpPostAction, OpenUriAction


def _get_exp_uri():
    """Return expected basic result for OpenUri action."""
    return OrderedDict((("@type", "OpenUri"),
                        ("name", "Open URL"),
                        ("targets",
                         [OrderedDict((("os", "default"),
                                       ("uri", "http://www.python.org")
                                       ))]
                         )))


def _get_exp_post():
    """Return expected basic result for HttpPost action."""
    return OrderedDict((("@type", "HttpPOST"),
                        ("name", "Run tests"),
                        ("target", "http://jenkins.com?action=trigger")))


def test_open_uri_action():
    e = _get_exp_uri()
    oua = OpenUriAction(name=e['name'], targets=e['targets'][0]['uri'])

    assert oua.json_payload == json.dumps(e)

    oua.add_target('android', 'http://www.python.org')
    e['targets'].append(OrderedDict((("os", "android"),
                                     ("uri", "http://www.python.org"))))
    assert oua.json_payload == json.dumps(e)

    e = _get_exp_uri()
    oua = OpenUriAction(name=e['name'],
                        targets={'default': e['targets'][0]['uri']})
    assert oua.json_payload == json.dumps(e)

    with pytest.raises(ValueError):
        oua.add_target('default', 'http://www.numpy.org')


def test_http_post_action():
    e = _get_exp_post()
    hpa = HttpPostAction(name=e['name'],
                         target=e['target'])
    assert hpa.json_payload == json.dumps(e)

    e['headers'] = [OrderedDict((('name', 'h_name'),
                                 ('value', 'h_value')))]

    hpa.set_headers({'h_name': 'h_value'})
    assert hpa.json_payload == json.dumps(e)

    hpa = HttpPostAction(name=e['name'],
                         target=e['target'])
    hpa.add_header({'h_name': 'h_value'})
    assert hpa.json_payload == json.dumps(e)

    e['headers'].append(OrderedDict((('name', 'h_name_2'),
                                     ('value', 'h_value_2'))))
    hpa.add_header({'h_name_2': 'h_value_2'})
    assert hpa.json_payload == json.dumps(e)

    e['body'] = 'Body content'
    hpa.set_body(e['body'])
    assert hpa.json_payload == json.dumps(e)

    e['bodyContentType'] = 'BodyContentType'
    hpa.set_body_content_type(e['bodyContentType'])
    assert hpa.json_payload == json.dumps(e)
