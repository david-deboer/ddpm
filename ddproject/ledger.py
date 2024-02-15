import pandas as pd
from copy import copy
from tabulate import tabulate
from dateutil.parser import parse
from . import ledger_settings as settings
from . import ledger_utils as LU


class Ledger():
    def __init__(self, designator, files, account_codes):
        """
        Parameters
        ----------
        designator : str
            Project designation, generally a fund number
        files : list of str
            List with the names of the files to be read in
        account_codes : dict
            Dictionary with budget fields as keys and account codes as values (list)
        """
        self.designator = designator
        self.files = files
        self.account_codes = account_codes

    def read_in_files(self, adjust={}):
        """
        Read in the datafiles to produce data dictionary
        """
        print("Reading in ledger files:", end=' ')
        self.data = {}
        self.first_date = parse('2030/1/1')
        self.last_date = parse('2000/1/1')
        self.grand_total = {'budget': 0.0, 'encumbrance': 0.0, 'actual': 0.0}
        self.total_entries = 0
        self.column_names = set()
        counters = {}
        for ledger_file, report_type in self.files.items():  # loop through files
            this_file = pd.read_csv(ledger_file)
            columns = this_file.columns.to_list()
            acct, column_map = settings.ledger_info(report_type)
            counters[ledger_file] = {'fy': 0, 'lines': 0}
            for row in this_file.values:  # loop through rows
                counters[ledger_file]['lines'] += 1
                this_account = LU.convert_value(acct['converter'], row[columns.index(acct['col'])])
                self.data.setdefault(this_account, {'entries': [], 'budget': 0.0,
                                                    'encumbrance': 0.0, 'actual': 0.0})
                this_entry = copy(settings.init_entry())
                for icol, ncol in enumerate(columns):  # loop through columns
                    entry_name, col_converter = column_map[ncol]
                    this_entry[entry_name] = LU.convert_value(col_converter, row[icol])
                    if entry_name in settings.amount_types and this_entry[entry_name] is None:
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
                if str(this_entry['fund']) != str(self.fund_number) and not self.override_fund_error:
                    raise ValueError(f"Fund {this_entry['fund']} != {self.fund_number}")
                # if fy.year is not None:  # check correct fiscal year
                #     if this_entry['date'] < fy.start or this_entry['date'] > fy.stop:
                #         if verbose:
                #             print(f"{newline}\t{this_entry['date'].isoformat().split('T')[0]} is not in FY{fy.year}")
                #         newline = ''
                #         counters[ledger_file]['fy'] += 1
            # if counters[ledger_file]['fy']:
            #     out_of_date = counters[ledger_file]['fy'] / counters[ledger_file]['lines']
            #     if out_of_date > 0.5:
            #         print(f"Warning!  {out_of_date*100:.1f} is more than 50%.")
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
