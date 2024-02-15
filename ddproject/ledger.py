import pandas as pd
from copy import copy
from tabulate import tabulate
from dateutil.parser import parse
from . import ledger_settings as settings
from . import ledger_utils as LU


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

    def read(self, adjust={}):
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
            fy = LU.get_fiscal_year(ledger_file)  # Will return the fiscal year if filename contains it
            this_file = pd.read_csv(ledger_file)
            columns = this_file.columns.to_list()
            self.columns[ledger_file] = columns
            acct, column_map = settings.ledger_info(report_type)
            counters[ledger_file] = {'fy': 0, 'lines': 0}
            for row in this_file.values:  # loop through rows
                counters[ledger_file]['lines'] += 1
                this_account = LU.convert_value(acct['converter'], row[columns.index(acct['col'])])
                self.data.setdefault(this_account, {'entries': []})
                for amtt in self.amount_types:
                    self.data[this_account][amtt] = 0.0
                this_entry = copy(settings.init_entry())
                for icol, ncol in enumerate(columns):  # loop through columns
                    entry_name, col_converter = column_map[ncol]
                    this_entry[entry_name] = LU.convert_value(col_converter, row[icol])
                    if entry_name in self.amount_types and this_entry[entry_name] is None:
                        this_entry[entry_name] = 0.0
                    if entry_name in settings.date_types and this_entry[entry_name] is None:
                        this_entry['date'] = parse('2010/1/1')
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

    def budget_categories(self, categories):
        self.categories = categories
        self.cat = {}
        for this_cat, these_codes in categories.items():
            self.cat[this_cat] = {}
            for amtt in self.amount_types:
                self.cat[this_cat][amtt] = 0.0
            for this_code in these_codes:
                for amtt in self.amount_types:
                    try:
                        self.cat[this_cat][amtt] += self.data[this_code][amtt]
                    except KeyError:
                        continue