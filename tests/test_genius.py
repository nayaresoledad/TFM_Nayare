import importlib


def test_buscar_cancion_found(monkeypatch):
    genius = importlib.import_module('extract_data.lyrics.obtener_letras.genius')

    class MockResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                'response': {
                    'hits': [
                        {'result': {'url': 'http://song', 'id': 123, 'full_title': 'Artist - Song'}}
                    ]
                }
            }

    monkeypatch.setattr('requests.get', lambda *args, **kwargs: MockResp())
    url, sid = genius.buscar_cancion('Artist', 'Song')
    assert url == 'http://song' and sid == 123


def test_buscar_cancion_not_found(monkeypatch):
    genius = importlib.import_module('extract_data.lyrics.obtener_letras.genius')

    class MockResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {'response': {'hits': []}}

    monkeypatch.setattr('requests.get', lambda *args, **kwargs: MockResp())
    url, sid = genius.buscar_cancion('Foo', 'Bar')
    assert url is None and sid is None
