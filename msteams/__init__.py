#!/usr/bin/env python

"""Wrapper objects for building and sending Message Cards."""

from collections import OrderedDict, namedtuple
import json
import requests
import types


Spec = namedtuple('Specification', ('expected_types', 'content'))
Spec.__new__.__defaults__ = (None, ) * len(Spec._fields)


def _snake_to_dromedary_case(string):
    """Convert snake_case to dromedaryCase."""
    words = string.split('_')
    if len(words) > 1:
        words[1:] = [w.title() for w in words[1:]]
    return ''.join(words)


def _viewitems(obj):
    """Python2/3 compatible iteration over ditionary."""
    func = getattr(obj, "viewitems", None)
    if not func:
        func = obj.items
    return func()


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

    def _set_field(self, field, value):
        """Set attribute of CardObject. Check that the value is."""
        if field not in self._fields:
            raise ValueError('Unknown field {}'.format(field))

        expected_types = self._fields[field].expected_types
        if not any([type(value) == ft for ft in expected_types]):
            raise TypeError('Got wrong type for field "{}" ({}). Expected {}'
                            .format(field, type(value), expected_types))

        # Check contents for lists/tuples
        content_type = self._fields[field].content
        if content_type is not None:
            if not all([isinstance(entry, content_type) for entry in value]):
                raise TypeError('All entries for {} should be of type {}'
                                .format(field, content_type))

        self._attrs[field] = value

    def __getitem__(self, key):
        """Return a field from CardObject."""
        return self._attrs[key]

    def __setitem__(self, key, value):
        """Set field to CardObject."""
        self._set_field(key, value)

    def __str__(self):
        """Return a string representation of the CardObject."""
        return '{}({})'.format(self.__class__.__name__,
                               ', '.join(self._attrs.keys()))

    def __repr__(self):
        """Return a string representation of the CardObject."""
        kv_paris = ['{} = {}'.format(k, v) for k, v in _viewitems(self._attrs)]
        return '{}({})'.format(self.__class__.__name__,
                               ', '.join(kv_paris))

    @property
    def payload(self):
        """Payload on python format."""
        return self.get_payload(fmt='python')

    @property
    def json_payload(self):
        """Payload on json format expected by Teams."""
        return self.get_payload(fmt='json')

    def get_payload(self, fmt='python'):
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
        if fmt == 'json':
            payload = json.dumps(payload)
        return payload


class ImageObject(CardObject):
    """Class representing a card image.

    See the Microsoft documentation for more details:
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#image-object
    """

    _fields = OrderedDict((
                ('image', Spec((str, ))),
                ('title', Spec((str, ))),
                ))

    def __init__(self, image, title=None):
        """Create image object."""
        super(ImageObject, self).__init__()

        self._set_field('image', image)
        if title is not None:
            self._set_field('title', title)


class Fact(CardObject):
    """Class wrapping a fact.

    See Microsoft documentation for more details:
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#section-fields
    """

    _fields = OrderedDict((
                ('name', Spec((str, ))),
                ('value', Spec((str, ))),
                ))

    def __init__(self, name, value):
        """Create fact object."""
        super(Fact, self).__init__()

        self._set_field('name', name)
        self._set_field('value', value)


class UriTarget(CardObject):
    """Class wrapping a URI target.

    See Microsoft documentation for more details:
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#openuri-action
    """
    _fields = OrderedDict((
                ('os', Spec((str, ))),
                ('uri', Spec((str, ))),
                ))

    def __init__(self, os, uri):
        super(UriTarget, self).__init__()

        self._set_field('os', os)
        self._set_field('uri', uri)


class Action(CardObject):
    """Base class for Action objects."""


class OpenUriAction(Action):
    """Open Uri action.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#openuri-action
    """

    _fields = OrderedDict((
                  ('name',    Spec((str, ))),
                  ('targets', Spec((tuple, list), UriTarget)),
                  ))

    def __init__(self, name, targets):
        """Create OpenUri action.

        name    -- The name displayed on the button. String
        targets -- The target URIs.
                   Either a string with the URI, or a dict with OS, URI pairs.
        https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#openuri-action
        """
        super(OpenUriAction, self).__init__()

        self._payload['@type'] = 'OpenUri'

        self._set_field('name', name)
        target_list = []
        if isinstance(targets, dict):
            for os, uri in _viewitems(targets):
                target_list.append(UriTarget(os=os, uri=uri))
        elif isinstance(targets, str):
            target_list.append(UriTarget(os='default', uri=targets))
        self._set_field('targets', target_list)

    def add_target(self, os, uri):
        """Add URI for a new target."""
        target_list = self._attrs.get('targets')
        os_list = [target['os'] for target in target_list]
        if os in os_list:
            raise ValueError('Target already set for {}'.format(os))
        target_list.append(UriTarget(os=os, uri=uri))


class Header(CardObject):
    """Class wrapping a header.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#header
    """
    _fields = OrderedDict((
                ('name', Spec((str, ))),
                ('value', Spec((str, ))),
                ))

    def __init__(self, name, value):
        super(Header, self).__init__()

        self._set_field('name', name)
        self._set_field('value', value)


class HttpPostAction(Action):
    """HTTP Post action
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#httppost-action
    """

    _fields = OrderedDict((
                  ('name',              Spec((str, ))),
                  ('target',            Spec((str, ))),
                  ('headers',           Spec((tuple, list, dict), Header)),
                  ('body',              Spec((str, ))),
                  ('body_content_type', Spec((str, ))),
                  ))

    def __init__(self, name, target):
        """Create OpenUri action.

        https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#httppost-action
        """
        super(HttpPostAction, self).__init__()

        self._payload['@type'] = 'HttpPOST'

        self._set_field('name', name)
        self._set_field('target', target)

    def set_headers(self, headers):
        """Set headers for HttpPostAction."""
        if isinstance(headers, dict):
            header_list = []
            for name, value in _viewitems(headers):
                header_list.append(Header(name=name, value=value))
        else:
            header_list = headers
        self._set_field('headers', header_list)

    def add_header(self, header):
        """Add header to header list."""
        header_list = self._attrs.get('headers', [])
        header_list.append(header)
        self._set_field('headers', header_list)

    def set_body(self, body):
        """Set body for HttpPostAction."""
        self._set_field('body', body)

    def set_body_content_type(self, body_content_type):
        """Set body for HttpPostAction."""
        self._set_field('body_content_type', body_content_type)


class CardSection(CardObject):
    """
    Class representing a card section of a MessageCard
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#section-fields
    """

    _fields = OrderedDict((
                ('title',             Spec((str, ))),
                ('start_group',       Spec((bool, ))),
                ('activity_image',    Spec((str, ))),
                ('activity_title',    Spec((str, ))),
                ('activity_subtitle', Spec((str, ))),
                ('activity_text',     Spec((str, ))),
                ('hero_image',        Spec((ImageObject, str))),
                ('text',              Spec((str, ))),
                ('facts',             Spec((tuple, list, dict), Fact)),
                ('potential_action',  Spec((tuple, list), Action)),
                ))

    def set_title(self, title):
        """Set section title."""
        self._set_field('title', title)

    def start_group(self):
        """Set section title."""
        self._set_field('start_group', True)

    def set_activity_image(self, image_url):
        """Set activity image for the section."""
        self._set_field('activity_image', image_url)

    def set_activity_title(self, title):
        """Set activity title for the section."""
        self._set_field('activity_title', title)

    def set_activity_subtitle(self, subtitle):
        """Set activity subtitle for the section."""
        self._set_field('activity_subtitle', subtitle)

    def set_activity(self, title=None, subtitle=None, image_url=None):
        """Set the activity for the card."""
        if title is not None:
            self.set_activity_title(title)
        if subtitle is not None:
            self.set_activity_subtitle(subtitle)
        if image_url is not None:
            self.set_activity_image(image_url)

    def set_hero_image(self, image, title=None):
        """Set hero image of section.

        image -- Image or image url as string.
        title -- Optional title. Only used if image is a string,
                 otherwise the title from Image is used
        """
        if not isinstance(image, ImageObject):
            image = ImageObject(image=image, title=title)
        self._set_field('hero_image', image)

    def set_text(self, text):
        """Set text for section."""
        self._set_field('text', text)

    def set_facts(self, facts):
        """Set section of facts.

        facts -- Can be a list/tuple of Facts, or a dict with key/value pairs.
        """
        if isinstance(facts, dict):
            facts = tuple(Fact(k, v) for k, v in _viewitems(facts))
        self._set_field('facts', facts)

    def add_fact(self, fact, value=None):
        """Append fact to facts section.

        fact -- Fact or fact name (str)
        value -- fact value. Only used if fact is a string.
        """
        facts = list(self._attrs.get('facts', []))
        if not isinstance(fact, Fact):
            fact = Fact(name=fact, value=value)
        facts.append(fact)
        self._set_field('facts', facts)

    def add_potential_action(self, potential_action):
        """Append a PotentialAction object to the section."""
        if not isinstance(potential_action, Action):
            raise TypeError('Expected Action, got {}'
                            .format(type(potential_action)))
        potential_actions = self._attrs.get('potential_action', [])
        potential_actions.append(potential_action)
        self._set_field('potential_action', potential_actions)


class MessageCard(CardObject):

    """
    Class representing a Micorsoft legacy message card
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference
    """
    _fields = OrderedDict((
                ('summary',           Spec((str, ))),
                ('title',             Spec((str, ))),
                ('text',              Spec((str, ))),
                ('theme_color',       Spec((str, ))),
                ('sections',          Spec((tuple, list), CardSection)),
                ('potential_actions', Spec((tuple, list), Action)),
                ))

    def __init__(self, **kwargs):
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

        self._payload['@type'] = 'MessageCard'
        self._payload['@context'] = 'https://schema.org/extensions'

    def set_summary(self, summary):
        """Set the summary line for the card."""
        self._set_field('summary', summary)

    def set_title(self, title):
        """Set the title for the card."""
        self._set_field('title', title)

    def set_text(self, text):
        """Set the text for the card."""
        self._set_field('text', text)

    def set_theme_color(self, theme_color):
        """Set the theme color for the card."""
        self._set_field('theme_color', theme_color)

    def set_sections(self, sections):
        """Set the sections for the card.

        sections -- List/tuple of CardSection objects.
        """
        self._set_field('sections', sections)

    def add_section(self, section):
        """Append a CardSection object to the card sections."""
        sections = self._attrs.get('sections', [])
        sections.append(section)
        self._set_field('sections', sections)

    def set_potential_actions(self, potential_actions):
        """Set the potential_actions list for the card.

        potential_actions -- List/tuple of PotentialAction objects.
        """
        self._set_field('potential_action', potential_action)

    def add_potential_action(self, potential_action):
        """Append a PotentialAction object to the card."""
        potential_actions = self._attrs.get('potential_actions', [])
        potential_actions.append(potential_action)
        self._set_field('potential_actions', potential_actions)


def send_message(card, channel):

    url = URL_MAP.get(channel, None)
    if url is None:
        raise ValueError('Invalid channel "{}". Supported channels are {}'
                         .format(channel, url_map.keys()))

    print(json.dumps(card.get_payload(), indent=4))

    response = requests.post(
        url, data=json.dumps(card.get_payload()),
        headers={'Content-Type': 'application/json'},
        proxies=PROXIES)

    if response.status_code != requests.codes.ok:
        raise ValueError(
            'Request to mattermost returned an error %s, the response is:\n%s'
            % (response.status_code, response.text))


if __name__ == '__main__':
    card = MessageCard(title='Descriptive title')
    card.set_summary('Brief summary')
    section = CardSection(title='Section title')
    section.set_hero_image('http://url', title='asdf')
    section.set_facts({'fact1': 'a', 'fact2': 'b'})
    section.add_fact('fact3', 'c')
    section.add_fact(Fact('fact4', 'd'))
    action = OpenUriAction('Open github', 'http://github.com')
    action.add_target('android', 'http://m.github.com')
    section.add_potential_action(action)

    post_action = HttpPostAction('Send comment', 'http://comment.com')
    post_action.set_headers({'http': 'yes', 'some_header': 'false'})
    post_action.add_header(Header('asdf', 'fdas'))
    section.add_potential_action(post_action)

    card.add_section(section)
    print(card.payload)
    print(card.json_payload)
    print(json.dumps(card.payload, indent=4))
    print(isinstance(OrderedDict(), dict))
