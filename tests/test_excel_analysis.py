import copy
import json
import shutil
from pathlib import Path

import openpyxl
import pytest

from investing_research.excel import read_inputs, recalculate, refresh
from investing_research.excel_layout import write_excel_model

ROOT = Path(__file__).resolve().parents[1]


def inputs():
    return json.loads((ROOT / 'examples/mlx/editions/2026-09-20-kiss/inputs.json').read_text())


def test_analysis_reconciles_and_refresh_preserves_it(tmp_path):
    if not shutil.which('soffice'):
        pytest.skip('LibreOffice required for real formula evaluation')
    data = inputs()
    path = tmp_path / 'analysis.xlsx'
    write_excel_model(data, path, presentation_version=3)
    actual, layout, _, _ = read_inputs(path)
    assert actual == data  # Historical exhibits cannot alter valuation assumptions.
    result = recalculate(path, tmp_path / 'recalc', 'base', layout['outputs']['active_case'])
    book = openpyxl.load_workbook(result, data_only=True)
    sheet = book['Analysis']
    assert sheet['B6'].value == 'H1 2025'
    assert sheet['C6'].value == 'H1 2026'
    assert sheet['B35'].value == pytest.approx(0, abs=1e-9)
    assert sheet['B46'].value == pytest.approx(0, abs=1e-9)
    assert sheet['B31'].value == pytest.approx(-4.211)
    assert sheet['B42'].value == pytest.approx(-23.608)
    assert sheet['C22'].value == pytest.approx(373.998)
    assert sheet['C20'].value == pytest.approx(126.515 / 103.905)
    source = tmp_path / 'inputs.json'
    source.write_text(json.dumps(data))
    refreshed = tmp_path / 'refresh.xlsx'
    refresh(path, source, refreshed)
    assert read_inputs(refreshed)[1]['presentation_version'] == 3
    modified = openpyxl.load_workbook(refreshed)
    modified['Analysis']['B31'] = '=999'
    modified.save(refreshed)
    with pytest.raises(ValueError, match='changed'):
        read_inputs(refreshed)


def test_analysis_rejects_ambiguous_or_incomparable_periods(tmp_path):
    data = inputs()
    data['historical'] = [f for f in data['historical'] if f['period'].startswith('H1 ')]
    duplicate = copy.deepcopy(next(f for f in data['historical'] if f['metric'] == 'revenue'))
    data['historical'].append(duplicate)
    with pytest.raises(ValueError, match='unambiguous'):
        write_excel_model(data, tmp_path / 'ambiguous.xlsx', presentation_version=3)
    data['historical'].pop()
    for fact in data['historical']:
        if fact['period'] == 'H1 2026':
            fact['ownership_basis'] = 'whole operation'
    with pytest.raises(ValueError, match='comparable'):
        write_excel_model(data, tmp_path / 'mismatch.xlsx', presentation_version=3)
