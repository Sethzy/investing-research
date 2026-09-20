import copy
import json
from pathlib import Path

import pytest

from investing_research.valuation_questions import annuity, calculate, project_hurdle, validate


def test_delayed_project_hurdle_prices_exactly_to_residual():
    cash = project_hurdle(120, 300, .5, .12, 12, 4, 30)
    npv = .5 * (cash * annuity(.12, 12, 4) - 300 - 30 / 1.12**15)
    assert npv == pytest.approx(120)
    assert project_hurdle(120, 300, .5, .12, 12, 5, 30) > cash
    assert project_hurdle(-120, 300, .5, 0, 10, 3, 20) == 32
    assert annuity(0, 8, 3) == 8


@pytest.mark.parametrize('args', [(0, 10, 0, .1, 10, 1, 0), (0, -1, .5, .1, 10, 1, 0),
                                 (0, 10, .5, -.1, 10, 1, 0), (0, 10, .5, .1, 0, 1, 0)])
def test_invalid_economics_rejected(args):
    with pytest.raises(ValueError):
        project_hurdle(*args)


def test_mlx_cash_and_conservative_liquidity():
    p = Path('examples/mlx/editions/2026-09-20-valuation-questions/questions/inputs.json')
    data = json.loads(p.read_text())
    actual = calculate(data)
    assert actual['adjusted_cash'] == pytest.approx([46.6028, 74.075])
    assert actual['cash_available'] == pytest.approx(254.168)
    assert actual['maximum_whole_capital'] == pytest.approx(508.336)
    data['drivers']['cash'] = 1
    actual = calculate(data)
    assert actual['cash_available'] == 0
    assert actual['existing_cash_shortfall'] > 0
    for key, value in [('shares', 0), ('investment_haircut', 1.1), ('life', 1.5)]:
        bad = copy.deepcopy(data)
        bad['drivers'][key] = value
        with pytest.raises(ValueError):
            validate(bad)


def test_companion_rejects_changed_formula_or_source(tmp_path):
    import shutil
    import openpyxl
    from investing_research.valuation_questions import verify_companion
    source = Path('examples/mlx/editions/2026-09-20-valuation-questions/questions')
    shutil.copytree(source, tmp_path / 'questions')
    folder = tmp_path / 'questions'
    assert verify_companion(folder)['status'] == 'pass'
    workbook = openpyxl.load_workbook(folder / 'questions.xlsx')
    workbook['Project hurdle']['B17'] = '=B16'
    workbook.save(folder / 'questions.xlsx')
    with pytest.raises(ValueError, match='input/formula changed'):
        verify_companion(folder)
