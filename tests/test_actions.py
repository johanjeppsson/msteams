import json
from collections import OrderedDict

import pytest

from msteams import HttpPostAction, OpenUriAction, TextInput, ActionCard


def _get_exp_uri():
    """Return expected basic result for OpenUri action."""
    return OrderedDict(
        (
            ("@type", "OpenUri"),
            ("name", "Open URL"),
            (
                "targets",
                [OrderedDict((("os", "default"), ("uri", "http://www.python.org")))],
            ),
        )
    )


def _get_exp_post():
    """Return expected basic result for HttpPost action."""
    return OrderedDict(
        (
            ("@type", "HttpPOST"),
            ("name", "Run tests"),
            ("target", "http://jenkins.com?action=trigger"),
        )
    )


def _get_exp_actioncard():
    """Return the expecdet basic result for ActionCard."""
    return OrderedDict(
        (
            ("@type", "ActionCard"),
            ("name", "Comment"),
            ("inputs", [OrderedDict((("@type", "TextInput"), ("id", "comment")))]),
            (
                "actions",
                [
                    OrderedDict(
                        (
                            ("@type", "HttpPOST"),
                            ("name", "Action's name prop."),
                            ("target", "https://yammer.com/comment?postId=123"),
                        )
                    )
                ],
            ),
        )
    )


def test_open_uri_action():
    e = _get_exp_uri()
    oua = OpenUriAction(name=e["name"], targets=e["targets"][0]["uri"])

    assert oua.json_payload == json.dumps(e)

    oua.add_target("android", "http://www.python.org")
    e["targets"].append(
        OrderedDict((("os", "android"), ("uri", "http://www.python.org")))
    )
    assert oua.json_payload == json.dumps(e)

    e = _get_exp_uri()
    oua = OpenUriAction(name=e["name"], targets={"default": e["targets"][0]["uri"]})
    assert oua.json_payload == json.dumps(e)

    with pytest.raises(ValueError):
        oua.add_target("default", "http://www.numpy.org")


def test_http_post_action():
    e = _get_exp_post()
    hpa = HttpPostAction(name=e["name"], target=e["target"])
    assert hpa.json_payload == json.dumps(e)

    e["headers"] = [OrderedDict((("name", "h_name"), ("value", "h_value")))]

    hpa.set_headers({"h_name": "h_value"})
    assert hpa.json_payload == json.dumps(e)

    hpa = HttpPostAction(name=e["name"], target=e["target"])
    hpa.add_header({"h_name": "h_value"})
    assert hpa.json_payload == json.dumps(e)

    e["headers"].append(OrderedDict((("name", "h_name_2"), ("value", "h_value_2"))))
    hpa.add_header({"h_name_2": "h_value_2"})
    assert hpa.json_payload == json.dumps(e)

    e["body"] = "Body content"
    hpa.set_body(e["body"])
    assert hpa.json_payload == json.dumps(e)

    e["bodyContentType"] = "BodyContentType"
    hpa.set_body_content_type(e["bodyContentType"])
    assert hpa.json_payload == json.dumps(e)


def test_action_card():
    e = _get_exp_actioncard()

    ip = TextInput(id=e["inputs"][0]["id"])
    post = HttpPostAction(
        name=e["actions"][0]["name"], target=e["actions"][0]["target"]
    )

    card = ActionCard(name=e["name"], inputs=ip, actions=post)
    assert card.json_payload == json.dumps(e)

    card = ActionCard(name=e["name"], inputs=ip, actions=post)
    card.set_name(e["name"])
    card.set_inputs(ip)
    card.set_actions(post)
    assert card.json_payload == json.dumps(e)

    card = ActionCard(name=e["name"], inputs=ip, actions=post)
    card.set_name(e["name"])
    card.add_inputs(ip)
    card.add_actions(post)
    assert card.json_payload == json.dumps(e)
