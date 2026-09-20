"""The release helper detects lost evidence pointers, beyond numeric parity."""
import hashlib
import json
import runpy
import shutil
from pathlib import Path

import openpyxl
import pytest

ROOT = Path(__file__).parents[1]
audit = runpy.run_path(str(ROOT / '.agents/skills/investing/scripts/audit_workbook.py'))['audit']


def test_reference_audit_does_not_claim_visual_or_live_approval():
    result = audit(ROOT / 'examples/mlx/model.json')
    assert result['structural_status'] == 'passed'
    assert result['live_recalculation']['status'] == 'not checked this run'
    assert result['visual_status'].startswith('pending')
    assert result['source_links_checked'] > 0
    assert result['source_comments_checked'] > 0


@pytest.mark.parametrize('damage', ['hyperlink', 'comment'])
def test_lost_provenance_fails_even_with_updated_workbook_hash(tmp_path, damage):
    for name in ('model.xlsx', 'model.json', 'inputs.json'):
        shutil.copy2(ROOT / 'examples/mlx' / name, tmp_path / name)
    path = tmp_path / 'model.xlsx'
    book = openpyxl.load_workbook(path)
    if damage == 'hyperlink':
        book['Historical']['H7'].hyperlink = 'https://example.invalid/wrong-source'
    else:
        cell = next(c for row in book['Assumptions'] for c in row if c.comment)
        cell.comment = None
    book.save(path)
    book.close()
    metadata = tmp_path / 'model.json'
    data = json.loads(metadata.read_text())
    data['workbook_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    metadata.write_text(json.dumps(data))
    result = audit(metadata)
    assert result['structural_status'] == 'failed'
    assert any(('source hyperlink' if damage == 'hyperlink' else 'source comment') in x for x in result['issues'])
