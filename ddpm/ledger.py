import pandas as pd
from copy import copy
from tabulate import tabulate
from . import settings_ledger as settings
from . import utils_time as ut
from . import utils_ledger as ul


class Ledger():
    def __init__(self, fund, files):
        """
        Parameters
        ----------
        fund : str
            Project designation, generally a fund number
        files : list of str
            List with the names of the files to be read

        Attributes
        ----------
        Same as Parameters

        """
        self.fund = fund
        self.files = files

    def read(self, invert=False):
        """
        Read in the datafiles to produce data dictionary

        Parameter
        ---------
        invert : bool
            Flag to invert the amount(s)

        Attributes
        ----------
        data : dict
            The ledger dictionary, generally keyed on account, then 'entries' and amount_types data['50000'] = {'entries': [], 'actual': 4567.8, ...}
        first_date/last_date : datetime
            Earliest and latest data entries
        grand_total : dict
            Totals of the various amount_types
        total_entries : int
            Total number of entries
        report_class : dict
            The per file report class, keyed on filename
        columns/amount_types/date_types : list
            The net set of columns/amount_types/date_types
            
        """
        print("Reading in ledger files:", end=' ')
        if invert:
            print("Inverting amounts")
        invert = -1.0 if invert else 1.0
        self.data = {}
        base = settings.BaseType()
        self.first_date = base.make_date('2040/1/1')
        self.last_date = base.make_date('2000/1/1')
        self.grand_total = {}
        self.total_entries = 0
        self.report_class = {}  # File report_type classes
        counters = {}  # out-of-fy and line counters for each file
        for key in ['columns', 'amount_types', 'date_types']:
            setattr(self, key, {})
        

        # Read in ledger files
        for ledger_file, report_type in self.files.items():  # loop through files
            if report_type == 'none':
                continue
            fy = ut.get_fiscal_year(ledger_file)  # Will return the fiscal year if filename contains it
            this_file = pd.read_csv(ledger_file)
            L = settings.ledger_info(report_type, this_file.columns.to_list())

            # Get overall info and initialize
            for key, value in L.reverse_map.items():  # Just in case there are multiple file types, etc
                self.columns[key] = value
                if key in L.amount_types:
                    self.amount_types[key] = value
                    if key not in self.grand_total:
                        self.grand_total[key] = 0.0
                if key in L.date_types:
                    self.date_types[key] = value
            self.report_class[ledger_file] = copy(L)
            counters[ledger_file] = {'fy': 0, 'lines': 0}

            # Loop over rows in the file
            for row in this_file.values:
                counters[ledger_file]['lines'] += 1
                this_account = L.keygen(row)
                if this_account not in self.data:
                    self.data[this_account] = {'entries': []}
                    for amtt in L.amount_types:
                        self.data[this_account][amtt] = 0.0
                this_entry = L.init()
                for icol, ncol in enumerate(L.columns):  # loop through columns
                    H = L.colmap[ncol]
                    if H['name'] in L.amount_types:
                        this_entry[H['name']] = invert * H['func'](row[icol])
                    else:
                        this_entry[H['name']] = H['func'](row[icol])
                self.data[this_account]['entries'].append(this_entry)
                self.total_entries += 1
                for col in L.amount_types:
                    self.data[this_account][col] += this_entry[col]
                    self.grand_total[col] += this_entry[col]
                for date_type in L.date_types:
                    if this_entry[date_type] < self.first_date:
                        self.first_date = copy(this_entry[date_type])
                    if this_entry[date_type] > self.last_date:
                        self.last_date = copy(this_entry[date_type])

                # A few specific checks
                try:
                    if str(this_entry['fund']) != str(self.fund):
                        raise ValueError(f"Fund {this_entry['fund']} != {self.fund}")
                except (KeyError, TypeError):
                    pass
                if fy.year is not None:  # check correct fiscal year
                    if this_entry['date'] < fy.start or this_entry['date'] > fy.stop:
                        print(f"\t{this_entry['date'].isoformat().split('T')[0]} is not in FY{fy.year}")
                        counters[ledger_file]['fy'] += 1
        table_data = []
        for lfile in sorted(counters):
            table_data.append([lfile, counters[lfile]['fy'], counters[lfile]['lines']])
        print('\n' + tabulate(table_data, headers=['ledger file', 'out_of_fy', 'total']))

    def update_account(self, accounts='all', shortcuts={}):
        """
        Go through ledger.data and change the key (account) if desired.

        Parameter
        ---------
        accounts : str, list
            Accounts to show for update
        shortcuts : dict or None
            Shortcuts to apply.

        """
        import csv, yaml
        from datetime import datetime
        self.updated = {}
        if accounts == 'all':
            accounts = None
        elif isinstance(accounts, str):
            accounts = accounts.split(',')
        if isinstance(shortcuts, str):
            with open(shortcuts, 'r') as fp:
                shortcuts = yaml.safe_load(fp)
        if len(shortcuts):
            print("Using shortcuts:")
            print(shortcuts)
        ctr = 0
        asking = True
        for account in self.data:
            if accounts is None or account in accounts:
                for entry in self.data[account]['entries']:
                    use_entry = copy(entry)
                    show = []
                    for col in self.columns:
                        if col in use_entry:
                            show.append(str(use_entry[col]))
                    show = '| '.join(show) + ':  '
                    if asking:
                        key = input(show)
                    else:
                        key = ''
                    if key == '-9':
                        print("Skipping the rest")
                        key = account
                        accounts = []
                        asking = False
                    if not len(key):
                        key = account
                    elif key in shortcuts:
                        key = shortcuts[key]
                    if key != account:
                        ctr += 1
                    self.updated.setdefault(key, {})
                    self.updated[key].setdefault('entries', [])
                    use_entry.update({'account': key})
                    self.updated[key]['entries'].append(use_entry)
            else:
                self.updated.setdefault(account, {})
                self.updated[account].setdefault('entries', [])
                for entry in self.data[account]['entries']:
                    self.updated[account]['entries'].append(copy(entry))
        if ctr:
            print(f"Made {ctr} updates -- writing 'updated.csv'.")
            with open('updated.csv', 'w') as fp:
                writer = csv.writer(fp)
                for account, entries in self.updated.items():
                    for entry in entries['entries']:
                        this_row = []
                        for col in self.columns:
                            this_one = entry[col]
                            if isinstance(this_one, datetime):
                                this_one = this_one.strftime('%m/%d/%Y')
                            this_row.append(this_one)
                        writer.writerow(this_row)

    def get_budget_categories(self, budget_categories):
        """
        Budget categories are groups of account codes which get sub-totaled.

        Generally the budget categories come from the yaml and are handled by manager.py.

        Parameter
        ---------
        budget_categories : dict, None
            keys are the budget_categories and values is a list of account codes

        Attributes
        ----------
        budget_categories : dict, None
            The budget_categories, budget_categories['staff'] = ['56789', ...]
        subtotals : dict
            Sub-totals for the budget categories, subtotals['staff']['actual'] = 12345.6

        """
        self.budget_categories = budget_categories
        self.subtotals = {}
        if budget_categories is None:
            return
        self.all_account_codes_in_included_categories = set()
        for this_cat, these_codes in self.budget_categories.items():
            self.subtotals[this_cat] = {}
            for amtt in self.grand_total:
                self.subtotals[this_cat][amtt] = 0.0
            for this_code in these_codes:
                self.all_account_codes_in_included_categories.add(this_code)
                if this_code not in self.data:
                    continue
                for amtt in self.grand_total:
                    self.subtotals[this_cat][amtt] += self.data[this_code][amtt]
        all_account_codes_in_data = set(list(self.data.keys()))
        not_included = list(all_account_codes_in_data - self.all_account_codes_in_included_categories)
        self.subtotals['not_included'] = {}
        for amtt in self.grand_total:
            self.subtotals['not_included'][amtt] = 0.0
        self.budget_categories['not_included'] = not_included
        for this_code in not_included:
            for amtt in self.grand_total:
                self.subtotals['not_included'][amtt] += self.data[this_code][amtt]

    def get_budget_aggregates(self, budget_aggregates):
        """
        Budget aggregates are groups of budget_categories which get sub-totaled.

        Generally the aggregates come from the yaml and are handled by manager.py

        Parameter
        ---------
        budget_aggregates : dict, None
            keys are the budget_aggregates and values is a list of budget_categories

        Attributes
        ----------
        budget_aggregates : dict, None
            The budget_aggregates, budget_aggregates['project_total'] = ['staff', 'equipment', ...]
        subtotals : dict
            Sub-totals for the budget categories, subtotals['project_total']['actual'] = 123.0

        """
        self.budget_aggregates = budget_aggregates
        if budget_aggregates is None:
            return
        for this_agg, these_cats in self.budget_aggregates.items():
            self.subtotals[this_agg] = {}
            for amtt in self.grand_total:
                self.subtotals[this_agg][amtt] = 0.0
                for cmp in these_cats:
                    self.subtotals[this_agg][amtt] += self.subtotals[cmp][amtt]

class Budget:
    def __init__(self, data):
        """
        Make the sponsor budget, generally from budget key in the yaml file

        Parameter
        ---------
        budget : dict
            Budget items and amounts or subtotaling list

        Attributes
        ----------
        categories : dict
            Budget categories, the value is just the same budget category.
        aggregates : dict
            Budget aggregates, the value is the list of comprising budget categories.
        budget : dict
            Dictionary of categories/aggregates with subtotals

        """
        self.budget = data['budget']
        self.categories = {}  # These are the budget categories (not aggregated as below)
        self.aggregates = {}  # These are aggregates of other budget categories
        self.grand_total = 0.0
        for this_cat, amt in self.budget.items():
            nval = amt
            if isinstance(amt, str):
                if amt[0] == '+':  # An aggregate
                    self.aggregates[this_cat] = amt.strip('+').split('+')
                    continue
                elif amt[0] == '=':  # Total from key amt
                    nval = ul.sumup(data[amt[1:]])
                else:
                    nval = eval(amt)
            self.categories[this_cat] = this_cat  # Just point to itself to make a dict
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