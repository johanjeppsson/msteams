from mock import patch
import msteams as ms


def test_send():
    with patch('msteams.request.urlopen', autospec=True) as mock_urlopen:

        card = ms.MessageCard(title='Title', summary='Summary')
        card.send('https://test.com')

        assert mock_urlopen.call_count == 1
        args, kwargs = mock_urlopen.call_args
        assert isinstance(args[0], ms.request.Request)


def test_send_proxy():
    with patch('msteams.request.urlopen', autospec=True) as mock_urlopen:
        card = ms.MessageCard(title='Title', summary='Summary')
        card.send('https://test.com', proxy='proxy')

        args, kwargs = mock_urlopen.call_args
        assert isinstance(args[0], ms.request.Request)

        card.send('https://test.com', proxy={'http': 'proxy'})

        assert mock_urlopen.call_count == 2
        args, kwargs = mock_urlopen.call_args
        assert isinstance(args[0], ms.request.Request)
