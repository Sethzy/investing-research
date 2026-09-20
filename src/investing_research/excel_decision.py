"""Decision diagnostics from existing model inputs; never a second valuation engine."""

import re


def write_decision(sheet, data, styles, formula, global_refs, outputs):
    facts = data['historical']
    # Scope is deliberately consolidated, reported history in the model currency.
    candidates = {}
    for index, fact in enumerate(facts):
        if (fact['basis'] == 'reported' and fact['ownership_basis'] == 'consolidated'
                and fact['unit'] == data['currency'] and fact['currency'] == data['currency']):
            candidates.setdefault((fact['entity'], fact['period']), {}).setdefault(fact['metric'], []).append(index + 7)

    def complete(rows, metrics):
        return all(len(rows.get(metric, [])) == 1 for metric in metrics)

    inventory = ('financial_assets_fvtpl', 'investment_in_associates')
    annual = ('net_operating_cash_flow', 'cash_paid_property_plant_equipment', 'cash_paid_mine_properties_development')
    periods = [(key, rows) for key, rows in candidates.items() if any(metric in rows for metric in inventory)]
    if not periods or len({key[0] for key, _ in periods}) != 1:
        raise ValueError('Decision needs one unambiguous consolidated investment-inventory period')

    def period_end(item):
        match = re.fullmatch(r'(FY|H1 |H2 )(\d{4})', item[0][1])
        if not match:
            raise ValueError('Decision inventory period must be FYyyyy or H1/H2 yyyy')
        return int(match[2]), 6 if match[1] == 'H1 ' else 12

    periods.sort(key=period_end)
    if len(periods) > 1 and period_end(periods[-1]) == period_end(periods[-2]):
        raise ValueError('Decision needs an unambiguous latest investment-inventory period')
    (entity, period), inventory_rows = periods[-1]
    if not complete(inventory_rows, inventory):
        raise ValueError('Decision latest inventory must be complete and unambiguous')
    years = sorted((int(key[1][2:]), rows) for key, rows in candidates.items()
                   if key[0] == entity and re.fullmatch(r'FY\d{4}', key[1]) and any(metric in rows for metric in annual))
    if len(years) < 2 or any(not complete(rows, annual) for _, rows in years[-2:]):
        raise ValueError('Decision needs two unambiguous comparable annual cash-flow periods')
    years = years[-2:]
    sheet.set_column('A:A', 48)
    sheet.set_column('B:C', 19)
    sheet.set_column('D:H', 7)
    sheet.freeze_panes(6, 1)
    sheet.set_row(3, 29)
    sheet.merge_range('A4:H4', f"PRICE, ASSETS AND EXPECTATIONS | {data['currency']}m except per-share figures", styles['section'])

    def line(row, label, expression, style='formula', col=1):
        sheet.write(row - 1, 0, label, styles['text'])
        formula('Decision', row - 1, col, expression, style)
        sheet.set_row(row - 1, 24)

    def reference(name):
        entry = outputs[name]
        return f"'{entry['sheet']}'!{entry['cell']}"

    quote = global_refs['reference_price']
    line(6, 'Selected operating case', '=Assumptions!B4', 'link')
    line(7, 'Reference price per share', f'=IF(ISNUMBER({quote}),{quote},"N/A")', 'link')
    sheet.merge_range('C7:H8', f"Quote date: {data.get('quote_date') or 'unavailable'}. Share count and balance-sheet dates may differ; see source comments and report.", styles['note'])
    line(8, 'Model share denominator, millions', f'={global_refs["diluted_shares"]}/1000000', 'link')
    line(9, 'Market equity using that denominator', '=IF(ISNUMBER(B7),B7*B8,"N/A")', 'total')
    line(11, 'Cash included in model', f'={global_refs["cash"]}/1000000', 'link')
    line(12, 'Debt included in model', f'={global_refs["debt"]}/1000000', 'link')
    line(13, 'Net cash', '=B11-B12', 'total')
    line(15, 'Selected operating-model enterprise value', f'={reference("enterprise_value")}/1000000', 'link')
    line(16, 'Other assets already in the model', f'={global_refs["other_assets"]}/1000000', 'link')
    line(17, 'Selected model equity value', '=B15+B13+B16', 'total')
    line(18, 'Market equity less selected model equity', '=IF(ISNUMBER(B9),B9-B17,"N/A")', 'total')
    sheet.merge_range('A20:H20', f'INVESTMENT INVENTORY | {period} carrying values; not current fair values', styles['section'])
    line(21, 'Financial assets at fair value through profit/loss', f'=Historical!C{inventory_rows[inventory[0]][0]}/1000000', 'link')
    line(22, 'Investments in associates', f'=Historical!C{inventory_rows[inventory[1]][0]}/1000000', 'link')
    line(23, 'Total disclosed carrying amounts', '=B21+B22', 'total')
    line(24, 'Residual after carrying amounts, if excluded', '=IF(AND(ISNUMBER(B18),B16=0),B18-B23,"N/A")', 'total')
    sheet.set_row(23, 34)
    sheet.merge_range('A26:H28', 'The residual is not Rentails value, an implied tin price or evidence of mispricing. Other assets are subtracted only when none are included in the operating model; otherwise N/A prevents double counting. Cash may be needed for development. Read the report for obligations and valuation gaps.', styles['note'])
    sheet.merge_range('A31:H31', 'HISTORICAL CASH CROSS-CHECK | observation, not normalized earnings', styles['section'])
    sheet.write('A33', 'Consolidated annual measure', styles['section'])
    for col, (year, rows) in enumerate(years, 1):
        letter = 'BC'[col - 1]
        sheet.write(32, col, f'FY{year}', styles['section'])
        for row, metric, label in [(34, annual[0], 'Operating cash flow'), (35, annual[1], 'Equipment payments'),
                                  (36, annual[2], 'Mine-development payments')]:
            line(row, label, f'=Historical!C{rows[metric][0]}/1000000', 'link', col)
        line(38, 'Cash after equipment and mine development', f'={letter}34-{letter}35-{letter}36', 'total', col)
        line(40, 'That cash / current market equity', f'=IF(AND(ISNUMBER($B$9),$B$9>0,{letter}38>0),{letter}38/$B$9,"N/A")', 'pct', col)
        line(41, 'Current market equity / that cash, times', f'=IF(AND(ISNUMBER($B$9),$B$9>0,{letter}38>0),$B$9/{letter}38,"N/A")', 'formula', col)
    for row in (37, 39, 40):
        sheet.set_row(row, 34)
    sheet.merge_range('A44:H47', 'These historical cash measures include corporate interest and tax timing, and precede other investments and financing. They are not distributable cash, forward yields or peer valuation multiples. Market equity is the matching numerator; do not use enterprise value with this cash series. Do not annualize a strong half-year without normalizing it.', styles['note'])
    sheet.merge_range('A49:H52', 'DECISION | Read the executive opinion in the matching report. A price-based rating requires supported remaining mine life, payable sales, capital and closure schedules, project economics, investments and current dilution. An illustrative operating model cannot determine Buy, Hold or Sell by itself.', styles['text'])
    sheet.print_area('A1:H53')
    sheet.set_landscape()
    sheet.set_h_pagebreaks([30])
    # Explicit scale preserves the intentional break in Excel and LibreOffice;
    # fit-to-height can move the final explanatory note onto an otherwise empty page.
    sheet.set_print_scale(70)
