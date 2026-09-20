import json
from types import SimpleNamespace
from unittest.mock import patch
from investing_research import x


def test_invalid_requests():
    assert x.search('')['error']['code'] == 'invalid_request'
    assert x.search('tin', count=101)['status'] == 'error'
    assert x.capture('https://evil.example/a/status/123')['status'] == 'error'


def test_missing_auth_is_sanitized():
    with patch.object(x.shutil, 'which', return_value='/node'), patch.object(x, '_credentials', side_effect=ValueError('secret-cookie')):
        result = x.search('tin')
    assert result['error']['code'] == 'credentials_unavailable'
    assert 'secret-cookie' not in json.dumps(result)


def test_search_capped_and_partial():
    payload = {'success': True, 'tweets': [{'id': '1', 'text': 'tin', 'author': {'username': 'miner'}, 'createdAt': 'Sun Sep 20 10:00:00 +0000 2026'}], 'has_more': True}
    with patch.object(x.shutil, 'which', return_value='/node'), patch.object(x, '_credentials', return_value={'authToken': 'secret', 'ct0': 'csrf'}), patch.object(x.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps(payload))) as run:
        result = x.search('tin', count=1)
    assert result['status'] == 'ok'
    assert result['coverage']['capped']
    assert not result['coverage']['exhaustive']
    assert result['posts'][0]['completeness'] == 'partial'
    assert result['posts'][0]['url'] == 'https://x.com/miner/status/1'
    assert 'secret' not in str(run.call_args.args)
    assert 'secret' not in json.dumps(result)


def test_upstream_failure_never_no_change():
    with patch.object(x.shutil, 'which', return_value='/node'), patch.object(x, '_credentials', return_value={}), patch.object(x.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='{"success":false,"error":"rate_limited"}')):
        result = x.search('tin')
    assert result['status'] == 'error'
    assert result['error']['code'] == 'rate_limited'


def test_explicit_session_requires_both_values(monkeypatch):
    monkeypatch.setenv('X_AUTH_TOKEN', 'secret')
    monkeypatch.delenv('X_CT0', raising=False)
    with patch.object(x.shutil, 'which', return_value='/node'):
        assert x.search('tin')['error']['code'] == 'credentials_unavailable'


def test_capture_remains_partial_and_preserves_conversation():
    payload = {'success': True, 'tweets': [{'id': '1', 'text': 'preview', 'article': {'title': 'Long article'}}], 'conversation': [{'id': '2', 'text': 'reply'}]}
    with patch.object(x.shutil, 'which', return_value='/node'), patch.object(x, '_credentials', return_value={}), patch.object(x.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps(payload))):
        result = x.capture('https://x.com/miner/status/1')
    assert result['posts'][0]['completeness'] == 'partial'
    assert result['conversation'][0]['id'] == '2'


def test_exact_full_post_normalization():
    result = x._normalize({'id': '1', 'text': 'full text', 'textCompleteness': 'complete'})
    assert result['completeness'] == 'complete'
    assert result['completeness_scope'] == 'post_text'
    assert result['thread_completeness'] == 'partial'


def test_capture_storage_preserves_scope(tmp_path):
    from investing_research.workspace import Workspace, read_json
    ws = Workspace(tmp_path)
    post = x._normalize({'id': '1', 'text': 'full text', 'textCompleteness': 'complete'})
    record, created = ws.capture_x(post)
    assert created
    assert record['completeness_scope'] == 'post_text'
    assert record['thread_completeness'] == 'partial'
    assert record['media_completeness'] == 'not_verified'
    raw = read_json(ws.inside(record['files'][0]))
    assert raw['completeness_scope'] == 'post_text'
    assert raw['completeness_reason']


def test_javascript_completeness_and_transient_retry_policy():
    import subprocess
    from pathlib import Path
    module = (Path(x.__file__).parent / 'vendor/x-policy.mjs').as_uri()
    script = '''
import {fetchWithTransientRetries, classifyText} from MODULE;
const full = classifyText({legacy:{truncated:false,full_text:'hello'}},{text:'hello'});
const absentFlag = classifyText({legacy:{full_text:'hello'}},{text:'hello'});
const ellipsis = classifyText({legacy:{full_text:'preview…'}},{text:'preview…'});
const truncated = classifyText({legacy:{truncated:true,full_text:'preview'}},{text:'preview'});
const article = classifyText({legacy:{truncated:false,full_text:'preview'},article:{}},{text:'preview'});
const note = classifyText({note_tweet:{note_tweet_results:{result:{text:'long full text'}}}},{text:'long full text'});
let calls = 0; await fetchWithTransientRetries(async()=>{calls++;return {status:503}},async()=>{});
let authCalls = 0; await fetchWithTransientRetries(async()=>{authCalls++;return {status:401}},async()=>{});
console.log(JSON.stringify({full,absentFlag,ellipsis,truncated,article,note,calls,authCalls}));
'''.replace('MODULE', json.dumps(module))
    result = json.loads(subprocess.check_output(['node', '--input-type=module', '-e', script], text=True))
    assert result['full']['textCompleteness'] == 'complete'
    assert result['absentFlag']['textCompleteness'] == 'complete'
    assert result['ellipsis']['textCompleteness'] == 'partial'
    assert result['note']['textCompleteness'] == 'complete'
    assert result['truncated']['textCompleteness'] == 'partial'
    assert result['article']['textCompleteness'] == 'partial'
    assert result['calls'] == 3
    assert result['authCalls'] == 1
