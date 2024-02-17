import pandas as pd
from copy import copy
from tabulate import tabulate
from dateutil.parser import parse
from . import settings_ledger as settings
from . import utils_ledger as ul
from . import utils_time as ut


class Ledger():
    amount_types = ['budget', 'encumbrance', 'actual']

    def __init__(self, fund, files):
        """
        Parameters
        ----------
        fund : str
            Project designation, generally a fund number
        files : list of str
            List with the names of the files to be read

        """
        self.fund = fund
        self.files = files

    def read(self):
        """
        Read in the datafiles to produce data dictionary

        """
        print("Reading in ledger files:", end=' ')
        self.data = {}
        self.first_date = parse('2040/1/1')
        self.last_date = parse('2000/1/1')
        self.grand_total = {}
        for amtt in self.amount_types:
            self.grand_total[amtt] =  0.0
        self.total_entries = 0
        self.columns = {}
        counters = {}
        for ledger_file, report_type in self.files.items():  # loop through files
            fy = ut.get_fiscal_year(ledger_file)  # Will return the fiscal year if filename contains it
            this_file = pd.read_csv(ledger_file)
            columns = this_file.columns.to_list()
            self.columns[ledger_file] = columns
            acct, column_map = settings.ledger_info(report_type)
            counters[ledger_file] = {'fy': 0, 'lines': 0}
            for row in this_file.values:  # loop through rows
                counters[ledger_file]['lines'] += 1
                this_account = ul.convert_value(acct['converter'], row[columns.index(acct['col'])])
                if this_account not in self.data:
                    self.data[this_account] = {'entries': []}
                    if not len(self.data[this_account]['entries']):
                        for amtt in self.amount_types:
                            self.data[this_account][amtt] = 0.0
                this_entry = copy(settings.init_entry())
                for icol, ncol in enumerate(columns):  # loop through columns
                    entry_name, col_converter = column_map[ncol]
                    this_entry[entry_name] = ul.convert_value(col_converter, row[icol])
                    if entry_name in self.amount_types and this_entry[entry_name] is None:
                        this_entry[entry_name] = 0.0
                    if entry_name in settings.date_types and this_entry[entry_name] is None:
                        this_entry['date'] = parse('2010/1/1')  # Make an outlier
                self.data[this_account]['entries'].append(this_entry)
                self.total_entries += 1
                for col in settings.amount_types:
                    self.data[this_account][col] += this_entry[col]
                    self.grand_total[col] += this_entry[col]
                if this_entry['date'] < self.first_date:
                    self.first_date = this_entry['date']
                if this_entry['date'] > self.last_date:
                    self.last_date = this_entry['date']
                if str(this_entry['fund']) != str(self.fund):
                    raise ValueError(f"Fund {this_entry['fund']} != {self.fund}")
                if fy.year is not None:  # check correct fiscal year
                    if this_entry['date'] < fy.start or this_entry['date'] > fy.stop:
                        print(f"\t{this_entry['date'].isoformat().split('T')[0]} is not in FY{fy.year}")
                        counters[ledger_file]['fy'] += 1
        table_data = []
        for lfile in sorted(counters):
            table_data.append([lfile, counters[lfile]['fy'], counters[lfile]['lines']])
        print('\n' + tabulate(table_data, headers=['ledger file', 'out_of_fy', 'total']))
        self.total_months = (self.last_date - self.first_date).days / 30.42  # close enough

    def get_budget_categories(self, budget_categories):
        """
        Budget categories are groups of account codes which get sub-totaled

        Parameter
        ---------
        budget_categories : dict, None
            keys are the budget_categories and values is a list of account codes

        Attributes
        ----------
        budget_categories : dict, None
            The budget_categories
        subtotals : dict
            Sub-totals for the budget categories

        """
        self.budget_categories = budget_categories
        self.subtotals = {}
        if budget_categories is None:
            return
        for this_cat, these_codes in self.budget_categories.items():
            self.subtotals[this_cat] = {}
            for amtt in self.amount_types:
                self.subtotals[this_cat][amtt] = 0.0
            for this_code in these_codes:
                if this_code not in self.data:
                    continue
                for amtt in self.amount_types:
                    self.subtotals[this_cat][amtt] += self.data[this_code][amtt]

    def get_budget_aggregates(self, budget_aggregates):
        """
        Budget aggregates are groups of budget_categories which get sub-totaled

        Parameter
        ---------
        budget_aggregates : dict, None
            keys are the budget_aggregates and values is a list of budget_categories

        Attributes
        ----------
        budget_aggregates : dict, None
            The budget_aggregates
        subtotals : dict
            Sub-totals for the budget categories

        """
        self.budget_aggregates = budget_aggregates
        if budget_aggregates is None:
            return
        for this_cat, cmps in self.budget_aggregates.items():
            self.subtotals[this_cat] = {}
            for amtt in self.amount_types:
                self.subtotals[this_cat][amtt] = 0.0
                for cmp in cmps:
                    self.subtotals[this_cat][amtt] += self.subtotals[cmp][amtt]

class Budget:
    def __init__(self, budget):
        """
        Make the sponsor budget.

        Parameter
        ---------
        budget : dict
            Budget items and amounts or subtotaling list
        Attributes:
            categories : dict
                Budget categories, the value is just the same budget category.
            aggregates : dict
                Budget aggregates, the value is the list of comprising budget categories.
            budget : dict
                Dictionary of categories/aggregates with subtotals

        """
        self.budget = budget
        self.categories = {}  # These are the budget categories (not aggregated as below)
        self.aggregates = {}  # These are aggregates of other budget categories
        self.grand_total = 0.0
        for this_cat, amt in self.budget.items():
            nval = amt
            if isinstance(amt, str):
                if amt[0] == '+':
                    self.aggregates[this_cat] = amt.strip('+').split('+')
                    continue
                else:
                    self.categories[this_cat] = copy(this_cat)
                    nval = eval(amt)
            else:
                self.categories[this_cat] = copy(this_cat)
            self.budget[this_cat] = nval
            try:
                self.grand_total += nval
            except ValueError:
                print(nval)
                continue
        for this_cat, cmps in self.aggregates.items():
            self.budget[this_cat] = 0.0
            for cmp in cmps:
                self.budget[this_cat] += self.budget[cmp]

    def adjust(self):
        print("")
        # if len(adjust):
        #     this_date = tdt.datetime.datetime.now()
        #     for account, val in adjust.items():
        #         this_entry = settings.init_entry({'account': account, 'date': this_date,
        #                                           'budget': 0.0, 'encumbrance': 0.0, 'actual': 0.0})
        #         for col, amt in val.items():
        #             this_entry[col] = amt
        #         self.data[account] = {'entries': [this_entry]}
        #         for col in settings.amount_types:
        #             self.data[account].setdefault(col, 0.0)
        #             self.data[account][col] += this_entry[col]
        #             self.grand_total[col] += this_entry[col]