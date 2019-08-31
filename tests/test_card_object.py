from collections import OrderedDict

import pytest

from msteams import CardObject, Fact, Field


class _TestObj(CardObject):

    _fields = OrderedDict((
        ('str', Field(str, False)),
        ('str_list', Field(str, True)),
        ('bool', Field(bool, False)),
        ('bool_list', Field(bool, True)),
        ('fact', Field(Fact, False)),
        ('fact_list', Field(Fact, True)),
        ))


def test_kwarg():
    obj = _TestObj()

    for field in obj._fields.keys():
        with pytest.raises(KeyError):
            obj[field]

    obj = _TestObj(str='a', str_list=['b', 'c'],
                   bool=False, bool_list=[True, False],
                   fact=Fact('a', 'b'), fact_list=[Fact('c', 'd')])
    assert obj['str'] == 'a'
    assert obj['str_list'] == ['b', 'c']
    assert obj['bool'] is False
    assert obj['bool_list'] == [True, False]
    assert obj['fact'] == Fact('a', 'b')
    assert obj['fact_list'] == [Fact('c', 'd')]

    # Check expansion to list
    obj = _TestObj(str_list='a')
    assert obj['str_list'] == ['a']


def test_equality():

    assert _TestObj(str='a') == _TestObj(str='a')
    assert _TestObj(str='a') != _TestObj(str='b')
    assert _TestObj(str='a') != Fact('a', 'b')
    assert _TestObj(str='a') != _TestObj(bool=False)


def test_value_check():

    with pytest.raises(ValueError):
        _TestObj(otherfield='False')

    with pytest.raises(TypeError):
        _TestObj(bool='False')

    with pytest.raises(TypeError):
        _TestObj(bool_list=[True, 'False'])


def test_set_get_item():

    obj = _TestObj(str='a', str_list=['b', 'c'],
                   bool=False, bool_list=[True, False],
                   fact=Fact('a', 'b'), fact_list=[Fact('c', 'd')])

    assert obj['str'] == 'a'
    obj['str'] = 'b'
    assert obj['str'] == 'b'

    assert obj['str_list'] == ['b', 'c']
    obj['str_list'] = ['d']
    assert obj['str_list'] == ['d']
    obj['str_list'] = 'd'
    assert obj['str_list'] == ['d']


def test_str():

    obj = _TestObj(str='a', str_list=['b', 'c'])

    assert str(obj) == "_TestObj(str, str_list)"
    assert repr(obj) == "_TestObj(str = a, str_list = ['b', 'c'])"
