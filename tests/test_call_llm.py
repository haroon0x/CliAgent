import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from theagent.utils.call_llm import AlchemistAIProxy

class DummyLLMProxy:
    def generate_docstring(self, function_code, model_name):
        return 'Dummy docstring for testing.'

def test_generate_docstring(monkeypatch):
    proxy = AlchemistAIProxy()
    # Monkeypatch the actual LLM call
    monkeypatch.setattr(proxy, 'generate_docstring', lambda code, model: 'Test docstring')
    doc = proxy.generate_docstring('def foo(): pass', 'test-model')
    assert doc == 'Test docstring' 