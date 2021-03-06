# -*- coding: UTF-8 -*-
from budget_app.loaders import SimpleBudgetLoader

import re


expenses_mapping = {
    'default': {'budget_line': 0, 'description': 2, 'budgeted_amount': 4, 'executed_amount': 5},
    '2019': {'budget_line': 0, 'description': 2, 'budgeted_amount': 3, 'executed_amount': 9},
    '2020': {'budget_line': 0, 'description': 2, 'budgeted_amount': 3, 'executed_amount': 9},
    '2021': {'budget_line': 0, 'description': 2, 'budgeted_amount': 3, 'executed_amount': 9},
}

income_mapping = {
    'default': {'budget_line': 0, 'description': 2, 'budgeted_amount': 4, 'executed_amount': 5},
    '2019': {'budget_line': 0, 'description': 2, 'budgeted_amount': 4, 'executed_amount': 6},
    '2020': {'budget_line': 0, 'description': 2, 'budgeted_amount': 4, 'executed_amount': 6},
    '2021': {'budget_line': 0, 'description': 2, 'budgeted_amount': 4, 'executed_amount': 6},
}

programme_mapping = {
    # old programme: new programme
}


class BudgetCsvMapper:
    def __init__(self, year, is_expense):
        column_mapping = income_mapping

        if is_expense:
            column_mapping = expenses_mapping

        mapping = column_mapping.get(str(year))

        if not mapping:
            mapping = column_mapping.get('default')

        self.budget_line = mapping.get('budget_line')
        self.description = mapping.get('description')
        self.budgeted_amount = mapping.get('budgeted_amount')
        self.executed_amount = mapping.get('executed_amount')


class HernaniBudgetLoader(SimpleBudgetLoader):
    # make year data available in the class and call super
    def load(self, entity, year, path, status):
        self.year = year
        SimpleBudgetLoader.load(self, entity, year, path, status)

    # Parse an input line into fields
    def parse_item(self, filename, line):
        # Ignore  non-data lines
        if not re.match(r'[12] ', line[0]):
            return None

        # Type of data
        is_expense = (filename.find('gastos.csv') != -1)
        is_actual = (filename.find('/ejecucion_') != -1)

        # Mapper
        mapper = BudgetCsvMapper(self.year, is_expense)

        # Budget line
        # We get the full budget line, so we have to split and amend
        budget_line = line[mapper.budget_line].split(' ')
        budget_line_codes = budget_line[1].split('.')

        # Income budget lines codes doesn't include institutional ones, and that
        # changes the shape of the codes string, so we need to amend it to allow
        # uniform processing
        if len(budget_line_codes) < 5:
            budget_line_codes.insert(0, '00')

        # Description
        description = line[mapper.description].strip()

        # Economic code
        ec_code = budget_line_codes[1]

        # Item numbers are the last two digits from the economic codes (fourth and fifth digits).
        # But, in order to differentiate items from past years with the same code (see #1070),
        # we add the year of the original budget the item comes from.
        original_year = budget_line[2]
        item_number = original_year + "/" + budget_line_codes[2]

        # Now, in order to make it a bit more obvious that some line items are from past years,
        # we add that at the end of their description.
        if original_year!=self.year:
            description = description + " (" + original_year + ")"

        # Institutional code
        # We got 2- digit codes (budget_line_codes[0]), that would correspond to
        # institutional codes, so we need to zfill them to get 3- digit codes
        ic_code = budget_line_codes[0].zfill(3)

        # Functional code
        # We got 5- digit functional codes as input or nothing for some income data
        fc_code = ''.join(budget_line_codes[3:5])

        # Parse amount
        amount = line[mapper.executed_amount if is_actual else mapper.budgeted_amount]
        amount = self._parse_amount(amount)

        # Expenses
        if is_expense:
            # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
            # mapping to be constant over time, we are forced to amend budget data prior to 2015.
            # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
            # For years before 2015 we check whether we need to amend the programme code
            if int(self.year) < 2015:
                fc_code = programme_mapping.get(fc_code, fc_code)

        # Income
        else:
            # Functional code
            # We don't need functional codes in income
            fc_code = None

        return {
            'is_expense': is_expense,
            'is_actual': is_actual,
            'fc_code': fc_code,
            'ec_code': ec_code,
            'ic_code': ic_code,
            'item_number': item_number,
            'description': description,
            'amount': amount
        }
