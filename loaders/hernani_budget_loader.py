# -*- coding: UTF-8 -*-
from budget_app.loaders import SimpleBudgetLoader


expenses_mapping = {
    'default': {'ic_code': 17, 'fc_code': 13, 'full_ec_code': 0, 'description': 2, 'forecast_amount': 4, 'actual_amount': 9},
}

income_mapping = {
    'default': {'ic_code': None, 'full_ec_code': 0, 'description': 3, 'forecast_amount': 4, 'actual_amount': 5},
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

        self.ic_code = mapping.get('ic_code')
        self.fc_code = mapping.get('fc_code')
        self.full_ec_code = mapping.get('full_ec_code')
        self.description = mapping.get('description')
        self.forecast_amount = mapping.get('forecast_amount')
        self.actual_amount = mapping.get('actual_amount')


class HernaniBudgetLoader(SimpleBudgetLoader):
    # make year data available in the class and call super
    def load(self, entity, year, path, status):
        self.year = year
        SimpleBudgetLoader.load(self, entity, year, path, status)

    # Parse an input line into fields
    def parse_item(self, filename, line):
        # Type of data
        is_expense = (filename.find('gastos.csv') != -1)
        is_actual = (filename.find('/ejecucion_') != -1)

        # Mapper
        mapper = BudgetCsvMapper(self.year, is_expense)

        # Description
        description = line[mapper.description].strip()

        # Parse amount
        amount = line[mapper.actual_amount if is_actual else mapper.forecast_amount]
        amount = self._parse_amount(amount)

        # Expenses
        if is_expense:
            # Institutional code
            # We got 2- or 4- digit institutional codes as input, but we only
            # need the first two, although we need to be able to represent the
            # number in just one char and then get a three digit code
            ic_code = line[mapper.ic_code].strip()
            ic_code = hex(int(ic_code[:2]))[2:].upper()
            ic_code = '0' + ic_code + '0'

            # Economic code
            # We get the full budget line, so we have to split and amend
            full_ec_code = line[mapper.full_ec_code].strip()
            full_ec_code = full_ec_code.split(" ")[1:-1][0]
            full_ec_code = full_ec_code.split(".")[1:3]
            full_ec_code = "".join(full_ec_code)

            # Concepts are the first three digits from the economic codes
            ec_code = full_ec_code[:3]

            # Item numbers are the last two digits from the economic codes (fourth and fifth digits)
            item_number = full_ec_code[-2:]

            # Functional code
            # We got 5- digit functional codes as input
            fc_code = line[mapper.fc_code].strip()

            # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
            # mapping to be constant over time, we are forced to amend budget data prior to 2015.
            # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
            # For years before 2015 we check whether we need to amend the programme code
            if int(self.year) < 2015:
                fc_code = programme_mapping.get(fc_code, fc_code)

        # Income
        else:
            # Institutional code
            # All income goes to the root node
            ic_code = '000'

            # Economic code
            # We get the full budget line, so we have to split and amend
            full_ec_code = line[mapper.full_ec_code].strip()
            full_ec_code = full_ec_code.split(" ")[1:-1][0]
            full_ec_code = full_ec_code.split(".")[:2]
            full_ec_code = "".join(full_ec_code)

            # Concepts are the first three digits from the economic codes
            ec_code = full_ec_code[:3]

            # Item numbers are the last two digits from the economic codes (fourth and fifth digits)
            item_number = full_ec_code[-2:]

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
