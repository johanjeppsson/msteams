#!/usr/bin/env python

from collections import OrderedDict
import json
import requests


def _snake_to_dromedary_case(string):
    words = string.split('_')
    if len(words) > 1:
        words[1:] = [w.title() for w in words[1:]]
    return ''.join(words)

def _viewitems(obj):
    """
    Python2/3 compatible iteration over ditionary.
    """
    func = getattr(obj, "viewitems", None)
    if not func:
        func = obj.items
    return func()


class CardObject(object):
    """Base class for card objects."""

    def __init__(self, **kwargs):

        self._payload = OrderedDict()
        self._attrs = {}

        for name, value in _viewitems(kwargs):
            self._set_field(name, value)

    def _set_field(self, name, value):
        """Set card attribute."""
        if name not in self._fields:
            raise ValueError('Unknown field {}'.format(name))

        expected_types = self._fields[name]['expected']
        if not any([type(value) == ft for ft in expected_types]):
            raise TypeError('Got wrong type for field "{}" ({}). Expected {}'
                            .format(name, type(value), expected_types))

        if 'content' in self._fields[name]:
            content_type = self._fields[name]['content']
            if not all([isinstance(entry, content_type) for entry in value]):
                raise TypeError('All entries for {} should be of type {}'
                                .format(name, content_type))

        self._attrs[name] = value

    def __getitem__(self, key):
        return self._attrs[key]

    def __setitem__(self, key, value):
        self._set_field(key, value)

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
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#image-object
    """
    _fields = OrderedDict((
                ('image', {'expected': (str, )}),
                ('title', {'expected': (str, )})
                ))

    def __init__(self, image, title=None):
        super(ImageObject, self).__init__()

        self._set_field('image', image)
        if title is not None:
            self._set_field('title', title)


class Fact(CardObject):
    """Class wrapping a fact.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#image-object
    """
    _fields = OrderedDict((
                ('name', {'expected': (str, )}),
                ('value', {'expected': (str, )})
                ))

    def __init__(self, name, value):
        super(Fact, self).__init__()

        self._set_field('name', name)
        self._set_field('value', value)


class UriTarget(CardObject):
    """Class wrapping a URI target.
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#image-object
    """
    _fields = OrderedDict((
                ('os', {'expected': (str, )}),
                ('uri', {'expected': (str, )})
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
                  ('name',    {'expected': (str, )}),
                  ('targets', {'expected': (list, )}),
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
                ('name', {'expected': (str, )}),
                ('value', {'expected': (str, )})
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
                  ('name',              {'expected': (str, )}),
                  ('target',            {'expected': (str, )}),
                  ('headers',           {'expected': (tuple, list),
                                         'content': Header}),
                  ('body',              {'expected': (str, )}),
                  ('body_content_type', {'expected': (str, )}),
                  ))

    def __init__(self, name, target):
        """Create OpenUri action.

        https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#httppost-action
        """
        super(HttpPostAction, self).__init__()

        self._payload['@type'] = 'HttpPOST'

        self._set_field('name', name)
        self._set_field('target', target)


class CardSection(CardObject):
    """
    Class representing a card section of a MessageCard
    https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference#section-fields
    """

    _fields = OrderedDict((
                ('title',             {'expected': (str, )}),
                ('start_group',       {'expected': (bool, )}),
                ('activity_image',    {'expected': (str, )}),
                ('activity_title',    {'expected': (str, )}),
                ('activity_subtitle', {'expected': (str, )}),
                ('activity_text',     {'expected': (str, )}),
                ('hero_image',        {'expected': (ImageObject, str)}),
                ('text',              {'expected': (str, )}),
                ('facts',             {'expected': (list, tuple, dict),
                                       'content': Fact}),
                ('potential_action',  {'expected': (list, tuple),
                                       'content': Action}),
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
                ('summary',           {'expected': (str, )}),
                ('title',             {'expected': (str, )}),
                ('text',              {'expected': (str, )}),
                ('theme_color',       {'expected': (str, )}),
                ('sections',          {'expected': (list, tuple),
                                       'content': CardSection}),
                ('potential_actions', {'expected': (list, tuple),
                                       'content': Action})
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
    post_action['body'] = 'Post body'
    section.add_potential_action(post_action)

    card.add_section(section)
    print(card.payload)
    print(card.json_payload)
    print(json.dumps(card.payload, indent=4))
    print(isinstance(OrderedDict(), dict))
