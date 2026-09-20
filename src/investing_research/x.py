"""Read-only X searches and post captures using vendored Bird; no API keys."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

_MESSAGES = {
    'authentication_failed': 'X session unavailable or expired. Sign in to the selected browser profile.',
    'credentials_unavailable': 'Cannot read X session. Sign in and verify browser profile and OS cookie access.',
    'dependency_missing': 'Install browser-cookie3 and Node.js 22 or later.',
    'rate_limited': 'X rate limit reached. Retry later.',
    'upstream_failed': 'X request failed. Coverage is unavailable; retry later or use browser capture.',
    'post_unavailable': 'Post unavailable; it may be restricted, deleted, or unsupported.',
    'invalid_request': 'Invalid query, count, browser, profile, or X post URL.',
}


def _error(code: str) -> dict:
    return {'status': 'error', 'posts': [], 'error': {'code': code, 'message': _MESSAGES.get(code, _MESSAGES['upstream_failed'])}, 'coverage': {'exhaustive': False, 'complete': False}}


def _cookie_path(browser: str, profile: str) -> Path:
    p = Path(profile).expanduser()
    if p.is_absolute():
        if p.is_file():
            return p
        base = p
    else:
        if p.name != profile or profile in ('.', '..'):
            raise ValueError('profile')
        if browser == 'firefox':
            raise ValueError('Firefox requires an absolute profile directory')
        if sys.platform == 'darwin':
            roots = {'chrome': 'Google/Chrome', 'brave': 'BraveSoftware/Brave-Browser', 'edge': 'Microsoft Edge'}
            base = Path.home() / 'Library/Application Support' / roots[browser] / profile
        elif sys.platform == 'win32':
            roots = {'chrome': 'Google/Chrome/User Data', 'brave': 'BraveSoftware/Brave-Browser/User Data', 'edge': 'Microsoft/Edge/User Data'}
            base = Path(os.environ.get('LOCALAPPDATA', '')) / roots[browser] / profile
        else:
            roots = {'chrome': 'google-chrome', 'brave': 'BraveSoftware/Brave-Browser', 'edge': 'microsoft-edge'}
            base = Path.home() / '.config' / roots[browser] / profile
    choices = [base / 'cookies.sqlite'] if browser == 'firefox' else [base / 'Network/Cookies', base / 'Cookies']
    return next((candidate for candidate in choices if candidate.is_file()), choices[0])


def _credentials(browser: str, profile: str | None) -> dict:
    # Explicit environment sessions are an optional alternative to browser extraction.
    auth, csrf = os.environ.get('X_AUTH_TOKEN'), os.environ.get('X_CT0')
    if auth or csrf:
        if not (auth and csrf):
            raise ValueError('incomplete session')
        return {'authToken': auth, 'ct0': csrf}
    import browser_cookie3
    kwargs = {'domain_name': 'x.com'}
    if profile:
        kwargs['cookie_file'] = str(_cookie_path(browser, profile))
    jar = getattr(browser_cookie3, browser)(**kwargs)
    values = {c.name: c.value for c in jar if c.domain.lstrip('.') in ('x.com', 'www.x.com') and c.name in ('auth_token', 'ct0') and not c.is_expired()}
    if not values.get('auth_token') or not values.get('ct0'):
        raise ValueError('missing session')
    return {'authToken': values['auth_token'], 'ct0': values['ct0']}


def _normalize(tweet: dict) -> dict:
    author = tweet.get('author') or {}
    timestamp = tweet.get('createdAt')
    if timestamp:
        try:
            timestamp = parsedate_to_datetime(timestamp).astimezone(timezone.utc).isoformat()
        except (ValueError, TypeError, OverflowError):
            pass
    identifier = str(tweet.get('id', ''))
    complete = tweet.get('textCompleteness') == 'complete'
    return {'id': identifier, 'url': f'https://x.com/{author.get("username", "i")}/status/{identifier}', 'text': tweet.get('text', ''), 'published_at': timestamp, 'author': author, 'completeness': 'complete' if complete else 'partial', 'completeness_scope': 'post_text', 'thread_completeness': 'partial', 'completeness_reason': 'Exact post text supplied by TweetDetail; media, thread and linked content excluded.' if complete else 'Accessible post text only; full post, thread, article and linked content completeness is not independently verified.', 'text_source': tweet.get('textSource'), 'source_truncated': tweet.get('sourceTruncated'), 'article': tweet.get('article'), 'conversation_id': tweet.get('conversationId'), 'in_reply_to': tweet.get('inReplyToStatusId')}


def _run(request: dict, browser: str, profile: str | None) -> dict:
    if browser not in ('chrome', 'brave', 'edge', 'firefox'):
        return _error('invalid_request')
    node = shutil.which('node')
    if not node:
        return _error('dependency_missing')
    try:
        cookies = _credentials(browser, profile)
    except ImportError:
        return _error('dependency_missing')
    except Exception:
        return _error('credentials_unavailable')
    script = Path(__file__).parent / 'vendor/x-detail.mjs'
    # Discard upstream diagnostics: errors can contain response bodies or credentials.
    env = {k: v for k, v in os.environ.items() if k not in ('AUTH_TOKEN', 'CT0', 'X_AUTH_TOKEN', 'X_CT0', 'BIRD_DEBUG_ARTICLE', 'BIRD_FEATURES_JSON', 'NODE_OPTIONS')}
    try:
        with tempfile.TemporaryDirectory(prefix='investing-bird-') as cache:
            env['BIRD_QUERY_IDS_CACHE'] = str(Path(cache) / 'queries.json')
            env['BIRD_FEATURES_CACHE'] = str(Path(cache) / 'features.json')
            proc = subprocess.run([node, str(script)], input=json.dumps({**request, 'cookies': cookies}), text=True, capture_output=True, timeout=180, env=env, check=False)
        payload = json.loads(proc.stdout)
        if proc.returncode or not payload.get('success'):
            return _error(payload.get('error', 'upstream_failed') if payload.get('error') in _MESSAGES else 'upstream_failed')
        posts = [_normalize(t) for t in payload.get('tweets', []) if t.get('id') and t.get('text')]
        count = request.get('count', 1)
        coverage = {'mode': 'Latest' if request['operation'] == 'search' else 'TweetDetail', 'requested_count': count, 'returned_count': len(posts), 'capped': bool(payload.get('has_more') or (request['operation'] == 'search' and len(posts) >= count)), 'exhaustive': False, 'complete': False}
        result = {'status': 'ok', 'posts': posts, 'coverage': coverage, 'retrieved_at': datetime.now(timezone.utc).isoformat()}
        if 'conversation' in payload:
            result['conversation'] = [_normalize(t) for t in payload['conversation'] if t.get('id') and t.get('text')]
        return result
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
        return _error('upstream_failed')


def search(query: str, *, count: int = 50, browser: str = 'chrome', profile: str | None = None) -> dict:
    """Retrieve bounded Latest results; a successful search is never exhaustive."""
    if not isinstance(query, str) or not query.strip() or len(query) > 2000 or type(count) is not int or not 1 <= count <= 100:
        return _error('invalid_request')
    return _run({'operation': 'search', 'query': query, 'count': count}, browser, profile)


def capture(url: str, *, browser: str = 'chrome', profile: str | None = None) -> dict:
    """Capture one exact X post and accessible conversation; completeness is partial."""
    match = re.fullmatch(r'https://(?:www\.)?(?:x\.com|twitter\.com)/[A-Za-z0-9_]+/status/(\d+)(?:[?][^\s]*)?', url or '')
    if not match:
        return _error('invalid_request')
    return _run({'operation': 'capture', 'tweet_id': match.group(1)}, browser, profile)
