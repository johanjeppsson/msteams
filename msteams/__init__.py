#!/usr/bin/env python

"""Wrapper objects for building and sending Message Cards."""

import json
from collections import OrderedDict, namedtuple

try:
    # Python 3
    from urllib import request
except ImportError:
    # Fallback to python 2
    import urllib2 as request

__version__ = "0.1.0"

Field = namedtuple("Specification", ("expected_type", "allow_iter", "valid_values"))
Field.__new__.__defaults__ = (None, False, None)


def _snake_to_dromedary_case(string):
    """Convert snake_case to dromedaryCase.

    >>> _snake_to_dromedary_case('snake_case')
    'snakeCase'
    >>> _snake_to_dromedary_case('longer_snake_case_name')
    'longerSnakeCaseName'
    """
    words = string.split("_")
    if len(words) > 1:
        words[1:] = [w.title() for w in words[1:]]
    return "".join(words)


def _viewitems(obj):
    """Python2/3 compatible iteration over ditionary."""
    func = getattr(obj, "viewitems", None)
    if not func:
        func = obj.items
    return func()


def _is_iter(val):
    """Check if value is of accepted iterable type."""
    return type(val) in [tuple, list]


class CardObject(object):
    """Base class for card objects."""

    def __init__(self, **kwargs):
        """Create CardObject.

        Any of the CardObject fields can be set as keyword arguments.
        """
        self._payload = OrderedDict()
        self._attrs = {}

        for name, value in _viewitems(kwargs):
            self._set_field(name, value)

    def _check_value(self, field, value):
        """Check if value is or or can be converted to the correct type."""
        if field not in self._fields:
            raise ValueError("Unknown field {}".format(field))

        exp_type = self._fields[field].expected_type
        allow_iter = self._fields[field].allow_iter
        valid_values = self._fields[field].valid_values

        if _is_iter(value) and allow_iter:
            wrong_types = [not isinstance(v, exp_type) for v in value]
            if any(wrong_types):
                wrong_type = type(value[wrong_types.index(True)])
                raise TypeError(
                    "Got iterable containing object of incorrect "
                    " type ({}). Expected {}".format(wrong_type, exp_type)
                )
            return value

        if not isinstance(value, exp_type):
            # Try to find converter
            conv_name = "from_{}".format(type(value).__name__)
            if not hasattr(exp_type, conv_name):
                raise TypeError(
                    "Got argument of wrong type ({}). Expected {}".format(
                        type(value), exp_type
                    )
                )
            value = getattr(exp_type, conv_name)(value)

        if valid_values is not None and value not in valid_values:
            raise ValueError(
                "Got invalid value for {}: ({}). "
                "Valid values are {}".format(field, value, valid_values)
            )

        if not _is_iter(value) and allow_iter:
            value = [value]

        return value

    def _set_field(self, field, value):
        """Sanitize and set attribute of CardObject."""

        sanitized_value = self._check_value(field, value)
        self._attrs[field] = sanitized_value

    def __getitem__(self, key):
        """Return a field from CardObject."""
        return self._attrs[key]

    def __setitem__(self, key, value):
        """Set field to CardObject."""
        self._set_field(key, value)

    def __str__(self):
        """Return a string representation of the CardObject."""
        pop_fields = [k for k in self._fields.keys() if k in self._attrs]
        return "{}({})".format(self.__class__.__name__, ", ".join(pop_fields))

    def __repr__(self):
        """Return a string representation of the CardObject."""
        pop_fields = [k for k in self._fields.keys() if k in self._attrs]
        kv_paris = ["{} = {}".format(k, self._attrs[k]) for k in pop_fields]
        return "{}({})".format(self.__class__.__name__, ", ".join(kv_paris))

    def __eq__(self, other):
        """Check for equality by checking that all set fields are equal."""
        if type(self) != type(other):
            return False

        for key in self._attrs.keys():
            if key not in other._attrs or self[key] != other[key]:
                return False

        return True

    def __ne__(self, other):
        """Not equals check."""
        return not self.__eq__(other)

    @property
    def payload(self):
        """Payload on python format."""
        return self.get_payload(fmt="python")

    @property
    def json_payload(self):
        """Payload on json format expected by Teams."""
        return self.get_payload(fmt="json")

    def get_payload(self, fmt="python", indent=None):
        """Return card payload on python or json format."""
        payload = self._payload.copy()
        for field_name in self._fields.keys():
            if field_name in self._attrs:
                value = self._attrs[field_name]
                if isinstance(value, CardObject):
                    value = value.payload
                if type(value) in (list, tuple):
                    value = [v.payload for v in value]
                payload[_snake_to_dromedary_case(field_name)] = value
        if fmt == "json":
            separators = (",", ": ") if indent is not None else (", ", ": ")
            payload = json.dumps(payload, indent=indent, separators=separators)
        return payload


class ImageObject(CardObject):
    """Class representing a card image.

    See the Microsoft documentation for more details:
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#image-object

    >>> im = ImageObject('http://www.image.com')
    >>> print(im.json_payload)
    {"image": "http://www.image.com"}
    >>> im.set_title('Image title')
    >>> print(im.json_payload)
    {"image": "http://www.image.com", "title": "Image title"}
    """

    _fields = OrderedDict((("image", Field(str, False)), ("title", Field(str, False))))

    def __init__(self, image, title=None):
        """Create image object."""
        super(ImageObject, self).__init__()

        self._set_field("image", image)
        if title is not None:
            self._set_field("title", title)

    @classmethod
    def from_dict(cls, d):
        """Create an ImageObject from dict."""
        title, image = list(_viewitems(d))[0]
        return ImageObject(image=image, title=title)

    @classmethod
    def from_str(cls, s):
        """Create an ImageObject from string."""
        return ImageObject(image=s)

    def set_title(self, title):
        """Set image title."""
        self._set_field("title", title)


class Fact(CardObject):
    """Class wrapping a fact.

    See Microsoft documentation for more details:
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#section-fields

    >>> f = Fact('name', 'value')
    >>> print(f.json_payload)
    {"name": "name", "value": "value"}
    """

    _fields = OrderedDict((("name", Field(str, False)), ("value", Field(str, False))))

    def __init__(self, name, value):
        """Create fact object."""
        super(Fact, self).__init__()

        self._set_field("name", name)
        self._set_field("value", value)

    @classmethod
    def from_dict(cls, d):
        """Create list of facts from dict."""
        facts = []
        for name, value in _viewitems(d):
            facts.append(Fact(name, value))
        return facts

    @classmethod
    def from_OrderedDict(cls, d):
        return Fact.from_dict(d)


class UriTarget(CardObject):
    """Class wrapping a URI target.

    See Microsoft documentation for more details:
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#openuri-action

    >>> ut = UriTarget(os='default', uri='http://www.python.org')
    >>> print(ut.json_payload)
    {"os": "default", "uri": "http://www.python.org"}
    >>> print(ut.payload)
    OrderedDict([('os', 'default'), ('uri', 'http://www.python.org')])
    """

    _fields = OrderedDict((("os", Field(str, False)), ("uri", Field(str, False))))

    def __init__(self, os, uri):
        super(UriTarget, self).__init__()

        self._set_field("os", os)
        self._set_field("uri", uri)

    @classmethod
    def from_dict(cls, d):
        """Create list of UriTargets from dict."""
        targets = []
        for name, value in _viewitems(d):
            targets.append(UriTarget(name, value))
        return targets

    @classmethod
    def from_str(cls, s):
        """Create list of UriTargets from string."""
        return UriTarget("default", s)


class Action(CardObject):
    """Base class for Action objects."""


class OpenUriAction(Action):
    """Open Uri action.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#openuri-action
    """

    _fields = OrderedDict(
        (("name", Field(str, False)), ("targets", Field(UriTarget, True)))
    )

    def __init__(self, name, targets):
        """Create OpenUri action.

        name    -- The name displayed on the button. String
        targets -- The target URIs.
                   Either a string with the URI, or a dict with OS, URI pairs.
        https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#openuri-action

        >>> action = OpenUriAction(name='Open URL', targets='http://www.python.org')
        >>> print(action.json_payload)
        {"@type": "OpenUri", "name": "Open URL", "targets": [{"os": "default", "uri": "http://www.python.org"}]}
        >>> action.add_target(os='android', uri='http://www.python.org')
        >>> print(action.json_payload)
        {"@type": "OpenUri", "name": "Open URL", "targets": [{"os": "default", "uri": "http://www.python.org"}, {"os": "android", "uri": "http://www.python.org"}]}
        >>> action = OpenUriAction(name='Open URL', targets={'default': 'http://www.python.org'})
        >>> print(action.json_payload)
        {"@type": "OpenUri", "name": "Open URL", "targets": [{"os": "default", "uri": "http://www.python.org"}]}
        """
        super(OpenUriAction, self).__init__()

        self._payload["@type"] = "OpenUri"

        self._set_field("name", name)
        self._set_field("targets", targets)

    def add_target(self, os, uri):
        """Add URI for a new target."""
        target_list = self._attrs.get("targets")
        os_list = [target["os"] for target in target_list]
        if os in os_list:
            raise ValueError("Target already set for {}".format(os))
        target_list.append(UriTarget(os=os, uri=uri))


class Header(CardObject):
    """Class wrapping a header.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#header

    """

    _fields = OrderedDict((("name", Field(str, False)), ("value", Field(str, False))))

    def __init__(self, name, value):
        """
        Create header object.

        >>> h = Header('Header name', 'Header value')
        >>> print(h.json_payload)
        {"name": "Header name", "value": "Header value"}
        """
        super(Header, self).__init__()

        self._set_field("name", name)
        self._set_field("value", value)

    @classmethod
    def from_dict(cls, d):
        """Create list of headers from dict."""
        headers = []
        for name, value in _viewitems(d):
            headers.append(Header(name, value))
        return headers


class HttpPostAction(Action):
    """HTTP Post action
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#httppost-action
    """

    _fields = OrderedDict(
        (
            ("name", Field(str, False)),
            ("target", Field(str, False)),
            ("headers", Field(Header, True)),
            ("body", Field(str, False)),
            ("body_content_type", Field(str, False)),
        )
    )

    def __init__(self, name, target, **kwargs):
        """Create HttpPost action.

        https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#httppost-action

        >>> action = HttpPostAction(name='Run tests', target='http://jenkins.com?action=trigger')
        >>> print(action.json_payload)
        {"@type": "HttpPOST", "name": "Run tests", "target": "http://jenkins.com?action=trigger"}
        >>> action.set_headers({'Header name': 'Header value'})
        >>> print(action.json_payload)
        {"@type": "HttpPOST", "name": "Run tests", "target": "http://jenkins.com?action=trigger", "headers": [{"name": "Header name", "value": "Header value"}]}
        >>> action.add_header({'header2': 'value2'})
        >>> print(action.json_payload)
        {"@type": "HttpPOST", "name": "Run tests", "target": "http://jenkins.com?action=trigger", "headers": [{"name": "Header name", "value": "Header value"}, {"name": "header2", "value": "value2"}]}
        >>> action.set_body('Body content')
        >>> print(action.get_payload(fmt='json', indent=4))
        {
            "@type": "HttpPOST",
            "name": "Run tests",
            "target": "http://jenkins.com?action=trigger",
            "headers": [
                {
                    "name": "Header name",
                    "value": "Header value"
                },
                {
                    "name": "header2",
                    "value": "value2"
                }
            ],
            "body": "Body content"
        }
        """
        super(HttpPostAction, self).__init__(**kwargs)

        self._payload["@type"] = "HttpPOST"

        self._set_field("name", name)
        self._set_field("target", target)

    def set_headers(self, headers):
        """Set headers for HttpPostAction."""
        self._set_field("headers", headers)

    def add_header(self, header):
        """Add header to header list."""
        header_list = self._attrs.get("headers", [])
        header = self._check_value("headers", header)
        header_list.extend(header)
        self._set_field("headers", header_list)

    def set_body(self, body):
        """Set body for HttpPostAction."""
        self._set_field("body", body)

    def set_body_content_type(self, body_content_type):
        """Set body for HttpPostAction."""
        self._set_field("body_content_type", body_content_type)


class Input(CardObject):
    """
    Class representing an Input object.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#inputs
    """

    _fields = OrderedDict(
        (
            ("id", Field(str, False)),
            ("is_required", Field(bool, False)),
            ("title", Field(str, False)),
            ("value", Field(str, False)),
        )
    )

    def set_id(self, id):
        """Set input id."""
        self._set_field("id", id)

    def set_is_required(self, is_required):
        """Set isRequired for input."""
        self._set_field("is_required", is_required)

    def set_title(self, title):
        """Set title for input."""
        self._set_field("title", title)

    def set_value(self, value):
        """Set value for input."""
        self._set_field("value", value)


class TextInput(Input):
    """
    Class representing a TextInput field.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#textinput
    """

    def __init__(self, **kwargs):
        sub_fields = OrderedDict(
            (("is_multiline", Field(bool, False)), ("max_length", Field(int, False)))
        )
        self._fields.update(sub_fields)
        super(TextInput, self).__init__(**kwargs)

        self._payload["@type"] = "TextInput"

    def set_is_multiline(self, is_multiline):
        """Set isMultiline for input."""
        self._set_field("is_multiline", is_multiline)

    def set_max_length(self, max_length):
        """Set maxLength for input."""
        self._set_field("max_length", max_length)


class DateInput(Input):
    """
    Class representing a DateInput field.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#dateinput
    """

    def __init__(self, **kwargs):
        self._fields["include_time"] = Field(bool, False)
        super(DateInput, self).__init__(**kwargs)

        self._payload["@type"] = "DateInput"

    def set_include_time(self, include_time):
        """Set includeTime for DateInput."""
        self._set_field("include_time", include_time)


class Choice(CardObject):
    """
    Class representing a key/value pair as a choice for MultipleChoiceInput.
    """

    _fields = OrderedDict(
        (("display", Field(str, False)), ("value", Field(str, False)))
    )

    def __init__(self, display, value):
        """
        Create choice object.

        >>> c = Choice('Choice 1', '1')
        >>> print(c.json_payload)
        {"display": "Choice 1", "value": "1"}
        """
        super(Choice, self).__init__()

        self._set_field("display", display)
        self._set_field("value", value)

    @classmethod
    def from_dict(cls, d):
        """Create list of choices from dict."""
        choices = []
        for display, value in _viewitems(d):
            choices.append(Choice(display, value))
        return choices


class MultipleChoiceInput(Input):
    """
    Class representing a MultipleChoiseInput.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#multichoiceinput
    """

    def __init__(self, **kwargs):
        sub_fields = OrderedDict(
            (
                ("choices", Field(Choice, True)),
                ("is_multi_select", Field(bool, False)),
                ("style", Field(str, False, ["normal", "expanded"])),
            )
        )
        self._fields.update(sub_fields)
        super(MultipleChoiceInput, self).__init__(**kwargs)

        self._payload["@type"] = "MultipleChoiceInput"

    def set_choices(self, choices):
        """Set choices for input."""
        self._set_field("choices", choices)

    def add_choices(self, choice):
        """Append choices to list."""
        choice = self._check_value("choices", choice)
        choice_list = list(self._attrs.get("choices", []))
        choice_list.extend(choice)
        self._set_field("choices", choice_list)

    def set_is_multi_select(self, is_multi_select):
        """Set isMultiSelect for intput."""
        self._set_field("is_multi_select", is_multi_select)

    def set_style(self, style):
        """Set style."""
        self._set_field("style", style)


class ActionCard(Action):
    """
    Class representing an ActionCard.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#actioncard-action
    """

    _fields = OrderedDict(
        (
            ("name", Field(str, False)),
            ("inputs", Field(Input, True)),
            ("actions", Field(Action, True)),
        )
    )

    def __init__(self, **kwargs):
        super(ActionCard, self).__init__(**kwargs)
        self._payload["@type"] = "ActionCard"

    def set_name(self, name):
        """Set name."""
        self._set_field("name", name)

    def set_inputs(self, inputs):
        self._set_field("inputs", inputs)

    def add_inputs(self, inputs):
        """Append inputs to ActionCard."""
        inputs = self._check_value("inputs", inputs)
        input_list = list(self._attrs.get("inputs", []))
        input_list.extend(inputs)
        self._set_field("inputs", inputs)

    def set_actions(self, actions):
        """Set action list for ActionCard."""
        self._set_field("actions", actions)

    def add_actions(self, actions):
        """Append actions to ActionCard."""
        actions = self._check_value("actions", actions)
        action_list = list(self._attrs.get("actions", []))
        action_list.extend(actions)
        self._set_field("actions", actions)


class CardSection(CardObject):
    """
    Class representing a card section of a MessageCard
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#section-fields
    """

    _fields = OrderedDict(
        (
            ("title", Field(str, False)),
            ("start_group", Field(bool, False)),
            ("activity_title", Field(str, False)),
            ("activity_subtitle", Field(str, False)),
            ("activity_image", Field(str, False)),
            ("activity_text", Field(str, False)),
            ("hero_image", Field(ImageObject, False)),
            ("text", Field(str, False)),
            ("facts", Field(Fact, True)),
            ("potential_action", Field(Action, True)),
        )
    )

    def set_title(self, title):
        """Set section title."""
        self._set_field("title", title)

    def start_group(self):
        """Set section title."""
        self._set_field("start_group", True)

    def set_activity_image(self, image_url):
        """Set activity image for the section."""
        self._set_field("activity_image", image_url)

    def set_activity_title(self, title):
        """Set activity title for the section."""
        self._set_field("activity_title", title)

    def set_activity_subtitle(self, subtitle):
        """Set activity subtitle for the section."""
        self._set_field("activity_subtitle", subtitle)

    def set_activity(self, title=None, subtitle=None, image_url=None):
        """Set the activity for the card."""
        if title is not None:
            self.set_activity_title(title)
        if subtitle is not None:
            self.set_activity_subtitle(subtitle)
        if image_url is not None:
            self.set_activity_image(image_url)

    def set_hero_image(self, image):
        """Set hero image of section.

        image -- ImageObject, image url as string or dict with {'title': 'url'}.
        """
        self._set_field("hero_image", image)

    def set_text(self, text):
        """Set text for section."""
        self._set_field("text", text)

    def set_facts(self, facts):
        """Set section of facts.

        facts -- Can be a list/tuple of Facts, or a dict with key/value pairs.
        """
        self._set_field("facts", facts)

    def add_fact(self, fact, value=None):
        """Append fact to facts section.

        fact -- Fact name (str)
        value -- fact value (str)
        """
        facts = list(self._attrs.get("facts", []))
        facts.append(Fact(name=fact, value=value))
        self._set_field("facts", facts)

    def add_facts(self, facts):
        """Append facts to card.

        facts: tuple or list containing Facts, or dict with key/value pairs.
        """
        fact_list = list(self._attrs.get("facts", []))
        fact_list.extend(self._check_value("facts", facts))
        self._set_field("facts", fact_list)

    def add_potential_action(self, potential_action):
        """Append a PotentialAction object to the section."""
        if not isinstance(potential_action, Action):
            raise TypeError("Expected Action, got {}".format(type(potential_action)))
        potential_actions = self._attrs.get("potential_action", [])
        potential_actions.append(potential_action)
        self._set_field("potential_action", potential_actions)


class MessageCard(CardObject):

    """
    Class representing a Micorsoft legacy message card
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference
    """

    _fields = OrderedDict(
        (
            ("summary", Field(str, False)),
            ("title", Field(str, False)),
            ("text", Field(str, False)),
            ("theme_color", Field(str, False)),
            ("sections", Field(CardSection, True)),
            ("potential_action", Field(Action, True)),
        )
    )

    def __init__(self, summary="Summary", **kwargs):
        """Create a new MessageCard.

        Keyword arguments:
        summary -- The summary line for the card. Should be a string
        title -- The card title. Should be a string
        text -- The main text of the card. Should be a string
        theme_color -- The theme color of the card. Should be a string
        sections -- The card sections. Should be a a list or tuple of
                    CardSection objects
        potential_actions -- The potential actions for the card.
                             Should be a list or tuple of PotentialAction
                             objects.

        See the documentation for message cards for more information about the
        fields:
        https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#card-fields
        """
        super(MessageCard, self).__init__(**kwargs)

        self._payload["@type"] = "MessageCard"
        self._payload["@context"] = "https://schema.org/extensions"

        self.set_summary(summary)

    def set_summary(self, summary):
        """Set the summary line for the card."""
        self._set_field("summary", summary)

    def set_title(self, title):
        """Set the title for the card."""
        self._set_field("title", title)

    def set_text(self, text):
        """Set the text for the card."""
        self._set_field("text", text)

    def set_theme_color(self, theme_color):
        """Set the theme color for the card."""
        self._set_field("theme_color", theme_color)

    def set_sections(self, sections):
        """Set the sections for the card.

        sections -- List/tuple of CardSection objects.
        """
        self._set_field("sections", sections)

    def add_section(self, section):
        """Append a CardSection object to the card sections."""
        sections = self._attrs.get("sections", [])
        sections.append(section)
        self._set_field("sections", sections)

    def set_potential_actions(self, potential_actions):
        """Set the potential_actions list for the card.

        potential_actions -- List/tuple of PotentialAction objects.
        """
        self._set_field("potential_action", potential_actions)

    def add_potential_action(self, potential_action):
        """Append a PotentialAction object to the card."""
        potential_actions = self._attrs.get("potential_action", [])
        potential_actions.append(potential_action)
        self._set_field("potential_action", potential_actions)

    def send(self, connector_url, proxy=None):
        """Send message card to Microsoft Teams webhook connector."""

        if proxy is not None:
            if not isinstance(proxy, dict):
                proxy = {"https": proxy}
            proxy_handler = request.ProxyHandler(proxy)
            opener = request.build_opener(proxy_handler)
            request.install_opener(opener)

        req = request.Request(
            connector_url,
            data=self.json_payload.encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        request.urlopen(req)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
