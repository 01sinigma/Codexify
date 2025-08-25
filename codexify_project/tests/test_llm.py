from codexify.utils.llm import LLMProvider
from codexify.systems.config_manager import get_config_manager


def test_llm_disabled_without_key():
    cm = get_config_manager()
    cm.set_session_override('llm.provider', 'none')
    cm.set_session_override('llm.api_key', '')
    llm = LLMProvider()
    out = llm.summarize('hi')
    assert 'disabled' in out.lower()


def test_llm_custom_mocked_urlopen():
    cm = get_config_manager()
    cm.set_session_override('llm.provider', 'custom')
    cm.set_session_override('llm.api_key', 'test')
    cm.set_session_override('llm.model', 'x')
    cm.set_session_override('llm.custom_url', 'http://example/api')
    llm = LLMProvider()

    import json as _json
    import urllib.request as _urllib

    class MockResp:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self):
            return _json.dumps({'content': 'OK'}).encode('utf-8')

    orig_urlopen = _urllib.urlopen
    try:
        _urllib.urlopen = lambda *args, **kwargs: MockResp()
        out = llm.summarize('ping', system='x')
        assert out.strip() == 'OK'
    finally:
        _urllib.urlopen = orig_urlopen


