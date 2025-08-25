import json
import ssl
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Tuple
import os
import time

from codexify.systems.config_manager import get_config_manager
from codexify.utils.logger import get_logger


class LLMProvider:
    """Minimal HTTP-based LLM provider (OpenAI, Gemini, Custom) without extra deps.
    Keeps everything in memory; API key is read from session overrides.
    """

    def __init__(self):
        self.cm = get_config_manager()
        self.log = get_logger('llm')
        # simple LRU cache
        self._cache: Dict[Tuple, str] = {}
        self._cache_order: list[Tuple] = []
        self._cache_capacity = 64
        self._last_call_ts = 0.0

    def _get_settings(self) -> Dict[str, Any]:
        provider = self.cm.get_setting('llm.provider', 'none')
        api_key = self.cm.get_setting('llm.api_key', '')
        # Fallback to environment variables if key empty
        if (not api_key) and provider:
            p = (provider or 'none').lower()
            if p == 'openai':
                api_key = os.getenv('OPENAI_API_KEY', '')
            elif p == 'gemini':
                api_key = os.getenv('GEMINI_API_KEY', '')
        self.log.debug(f"LLM settings loaded | provider={provider} model={self.cm.get_setting('llm.model','')} key_set={bool(api_key)}")
        return {
            'provider': provider,
            'api_key': api_key,
            'model': self.cm.get_setting('llm.model', 'gpt-4o-mini'),
            'temperature': float(self.cm.get_setting('llm.temperature', 0.2) or 0.2),
            'max_tokens': int(self.cm.get_setting('llm.max_tokens', 2000) or 2000),
            'safe_mode': bool(self.cm.get_setting('llm.safe_mode', True)),
            'custom_url': self.cm.get_setting('llm.custom_url', ''),
            'timeout': int(self.cm.get_setting('llm.timeout_sec', 60) or 60),
            'rate_limit_ms': int(self.cm.get_setting('llm.rate_limit_ms', 0) or 0),
            'gemini_thinking_budget': self.cm.get_setting('llm.gemini_thinking_budget', None),
        }

    def summarize(self, prompt: str, system: Optional[str] = None) -> str:
        cfg = self._get_settings()
        provider = (cfg['provider'] or 'none').lower()
        if provider in ('none', '') or not cfg['api_key']:
            return 'LLM is disabled or API key not set.'

        # apply rate limiting
        now = time.time()
        delay = max(0.0, (cfg['rate_limit_ms'] / 1000.0) - (now - self._last_call_ts))
        if delay > 0:
            time.sleep(delay)

        key = (provider, cfg['model'], prompt, system or '', cfg['temperature'], cfg['max_tokens'])
        if key in self._cache:
            # move to end (recent)
            try:
                self._cache_order.remove(key)
            except ValueError:
                pass
            self._cache_order.append(key)
            return self._cache[key]

        try:
            if provider == 'openai':
                out = self._call_openai(cfg, prompt, system)
            elif provider == 'gemini':
                out = self._call_gemini(cfg, prompt, system)
            elif provider == 'custom':
                out = self._call_custom(cfg, prompt, system)
            else:
                out = '[LLM provider not supported]'
            self.log.info(f"LLM call success | provider={provider} model={cfg['model']} len_prompt={len(prompt)}")
            self._last_call_ts = time.time()
            # cache store
            self._cache[key] = out
            self._cache_order.append(key)
            if len(self._cache_order) > self._cache_capacity:
                old = self._cache_order.pop(0)
                self._cache.pop(old, None)
            return out
        except Exception as e:
            self.log.error(f"LLM call error | provider={provider}: {e}")
            return f'[LLM error: {e}]'
        
    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        return self.summarize(prompt, system)

    def explain(self, prompt: str, system: Optional[str] = 'Explain in concise technical terms') -> str:
        return self.summarize(prompt, system)

    # --- Providers ---
    def _call_openai(self, cfg: Dict[str, Any], prompt: str, system: Optional[str]) -> str:
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': f"Bearer {cfg['api_key']}",
            'Content-Type': 'application/json',
        }
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        body = {
            'model': cfg['model'],
            'messages': messages,
            'temperature': cfg['temperature'],
            'max_tokens': cfg['max_tokens'],
        }
        data = json.dumps(body).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=cfg.get('timeout', 60)) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
            return payload.get('choices', [{}])[0].get('message', {}).get('content', '').strip() or '[empty]'

    def _call_gemini(self, cfg: Dict[str, Any], prompt: str, system: Optional[str]) -> str:
        # Gemini: Generative Language API (v1beta) content: generateContent
        model = cfg['model'] or 'gemini-1.5-flash'
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={cfg['api_key']}"
        headers = {'Content-Type': 'application/json'}
        parts = []
        if system:
            parts.append({'text': system})
        parts.append({'text': prompt})
        body = {
            'contents': [{'parts': parts}],
            'generationConfig': {
                'temperature': cfg['temperature'],
                'maxOutputTokens': cfg['max_tokens'],
            }
        }
        # Optional "thinking" budget for Gemini 2.5 models (if provided)
        try:
            tb = cfg.get('gemini_thinking_budget', None)
            if tb is not None:
                # REST field name is camelCase
                body['generationConfig']['thinkingConfig'] = {'thinkingBudget': float(tb)}
        except Exception:
            pass
        data = json.dumps(body).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=cfg.get('timeout', 60)) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
            candidates = payload.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    return (parts[0].get('text') or '').strip() or '[empty]'
            return '[empty]'

    def _call_custom(self, cfg: Dict[str, Any], prompt: str, system: Optional[str]) -> str:
        url = cfg['custom_url']
        if not url:
            raise RuntimeError('Custom URL is empty')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {cfg['api_key']}",
        }
        body = {
            'model': cfg['model'],
            'prompt': prompt,
            'system': system or '',
            'temperature': cfg['temperature'],
            'max_tokens': cfg['max_tokens'],
        }
        data = json.dumps(body).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=cfg.get('timeout', 60)) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
            return (payload.get('content') or '').strip() or '[empty]'

    # --- Discovery ---
    def list_models(self, provider: str) -> list[str]:
        """Return available model ids for a provider using public APIs.
        Requires API key to be present (from settings or environment).
        """
        cfg = self._get_settings()
        p = (provider or cfg.get('provider') or 'none').lower()
        api_key = cfg.get('api_key') or ''
        models: list[str] = []
        try:
            if p == 'openai' and api_key:
                req = urllib.request.Request(
                    'https://api.openai.com/v1/models',
                    headers={'Authorization': f'Bearer {api_key}'}
                )
                with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=cfg.get('timeout', 60)) as resp:
                    payload = json.loads(resp.read().decode('utf-8'))
                for item in payload.get('data', []):
                    mid = item.get('id') or ''
                    if isinstance(mid, str) and (mid.startswith('gpt-') or mid.startswith('o')):
                        models.append(mid)
            elif p == 'gemini' and api_key:
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                with urllib.request.urlopen(url, context=ssl.create_default_context(), timeout=cfg.get('timeout', 60)) as resp:
                    payload = json.loads(resp.read().decode('utf-8'))
                for item in payload.get('models', []):
                    name = item.get('name') or ''  # e.g., models/gemini-1.5-pro
                    if isinstance(name, str) and 'gemini' in name:
                        models.append(name.split('/')[-1])
        except Exception:
            # ignore discovery errors, return what we have
            pass
        # Deduplicate while preserving order
        seen = set()
        out = []
        for m in models:
            if m not in seen:
                seen.add(m)
                out.append(m)
        return out
