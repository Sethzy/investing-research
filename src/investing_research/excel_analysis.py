"""Comparable historical exhibits, separate from forecast assumptions."""

import math
import re


def write_analysis(wb, sheet, data, styles, formula):
    facts = data['historical']
    metrics = ('revenue', 'gross_profit', 'profit_before_tax', 'income_tax_expense', 'net_income',
               'net_operating_cash_flow', 'cash_paid_property_plant_equipment',
               'cash_paid_mine_properties_development', 'net_investing_cash_flow',
               'net_financing_cash_flow', 'opening_cash_and_cash_equivalents')
    # Only compare matching period types, entity, ownership and currency. Ambiguity fails closed.
    candidates = {}
    for index, fact in enumerate(facts):
        if fact['metric'] in metrics and fact['unit'] == data['currency'] and fact['currency'] == data['currency']:
            key = (fact['period'], fact['entity'], fact['ownership_basis'], fact['basis'])
            candidates.setdefault(key, {}).setdefault(fact['metric'], []).append(index + 7)
    groups = {}
    for key, rows in candidates.items():
        match = re.fullmatch(r'(H[12] |FY)(\d{4})', key[0])
        if match and all(len(rows.get(metric, [])) == 1 for metric in metrics):
            groups.setdefault((match[1], *key[1:]), []).append((int(match[2]), key, rows))
    groups = [sorted(group) for group in groups.values() if len(group) >= 2]
    if not groups:
        raise ValueError('Analysis needs two unambiguous comparable reported periods in the model currency')
    selected = max(groups, key=lambda group: (group[-1][0], group[-1][1][0].startswith('H')))[-2:]
    sheet.set_column('A:A', 43)
    sheet.set_column('B:C', 18)
    sheet.set_column('D:D', 17)
    sheet.set_column('E:I', 8)
    sheet.set_zoom(90)
    sheet.merge_range('A4:I4', f"Reported history | {selected[0][1][0]} versus {selected[1][1][0]} | {data['currency']} millions", styles['section'])
    sheet.set_row(3, 24)
    labels = ('Revenue', 'Gross profit', 'Profit before tax', 'Income tax expense', 'Net profit',
              'Operating cash flow', 'Equipment spending', 'Mine-development spending',
              'Investing cash flow', 'Financing cash flow', 'Opening cash')
    sheet.write('A6', 'Reported measure', styles['section'])
    for col, (_, key, _) in enumerate(selected, 1):
        sheet.write(5, col, key[0], styles['section'])
    sheet.write('D6', 'Change', styles['section'])
    for row, (metric, label) in enumerate(zip(metrics, labels), 6):
        sheet.write(row, 0, label, styles['text'])
        for col, (_, _, lookup) in enumerate(selected, 1):
            formula('Analysis', row, col, f'=Historical!C{lookup[metric][0]}/1000000', 'link')
        formula('Analysis', row, 3, f'=C{row+1}-B{row+1}')
    for row, label, expression, style in [
        (18, 'Gross margin', '{c}8/{c}7', 'pct'),
        (19, 'Cash flow / net profit', '{c}12/{c}11', 'formula'),
        (20, 'Operating cash less mine/equipment spend', '{c}12-{c}13-{c}14', 'total'),
        (21, 'Closing cash (reconciled)', '{c}17+{c}12+{c}15+{c}16', 'total'),
    ]:
        sheet.write(row, 0, label, styles['text'])
        sheet.set_row(row, 30)
        for col, letter in ((1, 'B'), (2, 'C')):
            expr = expression.format(c=letter)
            # Negative/zero earnings make the cash conversion ratio misleading.
            if row in (18, 19):
                denominator = 7 if row == 18 else 11
                expr = f'IF({letter}{denominator}>0,{expr},"N/A")'
            formula('Analysis', row, col, '=' + expr, style)
    sheet.merge_range('A24:I25', 'Cash conversion is a diagnostic, not an earnings-quality score. Cash after equipment and mine spending still precedes other investing uses and financing. Periods and ownership match; historical values are not forecasts.', styles['note'])
    sheet.merge_range('A27:I27', 'WHY PROFIT CHANGED | accounting bridge, not a price/volume attribution', styles['section'])
    bridge = [('Prior net profit', '=B11'), ('Gross profit change', '=C8-B8'),
              ('Other pre-tax changes, net', '=(C9-C8)-(B9-B8)'),
              ('Tax expense change', '=B10-C10'), ('Current net profit', '=C11')]
    for row, (label, expr) in enumerate(bridge, 28):
        sheet.write(row, 0, label, styles['text'])
        formula('Analysis', row, 1, expr, 'total' if row in (28, 32) else 'formula')
        sheet.set_row(row, 23)
    sheet.write('A35', 'Profit bridge residual (must be zero)', styles['text'])
    formula('Analysis', 34, 1, '=SUM(B29:B32)-B33')
    sheet.merge_range('A37:I37', 'WHERE CASH WENT | current period', styles['section'])
    cash = [('Opening cash', '=C17'), ('Operating cash flow', '=C12'),
            ('Equipment and mine development', '=-C13-C14'),
            ('Other investing cash flow, net', '=C15+C13+C14'),
            ('Financing cash flow', '=C16'), ('Closing cash', '=C22')]
    for row, (label, expr) in enumerate(cash, 38):
        sheet.write(row, 0, label, styles['text'])
        formula('Analysis', row, 1, expr, 'total' if row in (38, 43) else 'formula')
        sheet.set_row(row, 23)
    sheet.write('A46', 'Cash bridge residual (must be zero)', styles['text'])
    formula('Analysis', 45, 1, '=SUM(B39:B43)-B44')
    for start, end, anchor, title in [(28, 32, 'E28', 'Profit bridge components'), (38, 43, 'E38', 'Cash bridge components')]:
        chart = wb.add_chart({'type': 'bar'})
        chart.add_series({'categories': ['Analysis', start, 0, end, 0], 'values': ['Analysis', start, 1, end, 1], 'fill': {'color': '#087C86'}, 'border': {'none': True}})
        chart.set_title({'name': title + f" ({data['currency']}m)", 'name_font': {'size': 10}})
        chart.set_legend({'none': True})
        current = selected[-1][2]
        def value(metric):
            return facts[current[metric][0] - 7]['value'] / 1000000
        extent = abs(value('net_income')) if start == 28 else abs(value('opening_cash_and_cash_equivalents') + value('net_operating_cash_flow') + value('net_investing_cash_flow') + value('net_financing_cash_flow'))
        step = 10 ** math.floor(math.log10(max(extent / 3, 0.01)))
        interval = math.ceil(max(extent / 3, 0.01) / step) * step
        chart.set_x_axis({'name': f"{data['currency']}m", 'num_format': '0.##', 'num_font': {'size': 8}, 'major_unit': interval})
        chart.set_y_axis({'num_font': {'size': 8}})
        chart.set_size({'width': 275, 'height': 200})
        sheet.insert_chart(anchor, chart)
    sheet.merge_range('A49:I51', 'Read the report for tax effects, collection timing and capital-allocation judgments. Other pre-tax changes are an explicitly aggregated residual; their components need source review. The cash bridge is not a reconciliation from profit to operating cash.', styles['note'])
    sheet.set_landscape()
    sheet.print_area('A1:I52')
    sheet.set_h_pagebreaks([26])
    sheet.fit_to_pages(1, 2)
