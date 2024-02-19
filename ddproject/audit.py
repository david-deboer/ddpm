"""
This holds the time plots, detail lists etc. for ledger

"""
import numpy as np
from copy import copy
from tabulate import tabulate
from . import utils_ledger as ul
from . import utils_time as ut
from . import plots_ledger as pl
from dateutil.parser import parse
from datetime import datetime


class Filter:
    def __init__(self, ledger_keys):
        """
        Parameter
        ---------
        ledger_keys : list
            Full list of ledger keys (accounts)

        """
        self.ledger_keys = ledger_keys
        self.absval = {}
        self.amt_min = {}
        self.amt_max = {}
        self.reset()

    def reset(self):
        self.set_account('all')
        self.set_actual('all')
        self.set_budget('all')
        self.set_encumbrance('all')
        self.set_date('all')
        self.set_exclude(None)
        self.other = {}

    def check(self, data):
        if data['date'] < self.date_min or data['date'] > self.date_max:
            return False
        this = {}
        for amt in ['actual', 'budget', 'encumbrance']:
            this[amt] = abs(data[amt]) if self.absval[amt] else data[amt]
            if this[amt] < self.amt_min[amt] or this[amt] > self.amt_max[amt]:
                return False
        for key, val in self.other.items():
            if isinstance(val, list) and data[key] not in val:
                return False
            elif data[key] != val:
                return False
        return True

    def set(self, **kwargs):
        for key, value in kwargs.items():
            try:
                getattr(self, f"set_{key}")(value)
            except AttributeError:
                self.other[key] = value
            
    def _set_accounts(self,key, val):
        if isinstance(val, str):
            if val.lower() == 'all':
                setattr(self, key, self.ledger_keys)
            elif val.lower() == 'none':
                setattr(self, key, [])
            else:
                setattr(self, key, val.split(','))
        elif isinstance(val, list):
            setattr(self, key, [str(x) for x in val])
        elif val is None:
            setattr(self, key, [])
    
    def set_account(self, val):
        self._set_accounts('account', val)

    def set_exclude(self, val):
        self._set_accounts('exclude', val)

    def set_date(self, val):
        val = 'all' if val is None else val
        self.date_min = datetime(year=2000, month=1, day=1).astimezone()
        self.date_max = datetime(year=2100, month=12, day=31).astimezone()
        if val == 'all':
            return
        try:
            val = parse(val)
        except parse.ParserError:
            pass
        if isinstance(val, datetime):
            self.date_min = datetime(year=val.year, month=val.month, day=val.day, hour=0, minute=0, second=0).astimezone()
            self.date_max = datetime(year=val.year, month=val.month, day=val.day, hour=23, minute=59, second=59).astimezone()
        else:
            self.date_min, self.date_max = [parse(x).astimezone() for x in val.split('_')]

    def _set_amount(self, key, val):
        """

        """
        self.absval[key] = False
        self.amt_min[key] = -1E15
        self.amt_max[key] = 1E15
        val = 'all' if val is None else val
        try:
            val = float(val)
        except ValueError:
            pass

        if isinstance(val, str):
            if val.lower() == 'all':
                return
            if '|' in val:
                self.absval[key] = True
                val.replace('|', '')
            if val.startswith('<'):
                self.amt_max[key] = float(val.replace(',', '').replace('$', '').replace('<', ''))
            elif val.startswith('>'):
                self.amt_min[key] = float(val.replace(',', '').replace('$', '').replace('>', ''))
            elif '_' in val:
                self.amt_min[key], self.amt_max[key] = [float(x.replace(',', '').replace('$', '')) for x in val.split('_')]
        else:  # Within a dollar
            self.amt_min[key] = val - 1.0
            self.amt_max[key] = val + 1.0


    def set_actual(self, val):
        self._set_amount('actual', val)

    def set_encumbrance(self, val):
        self._set_amount('encumbrance', val)

    def set_budget(self, val):
        self._set_amount('budget', val)


class Audit():
    """
    Look at the new CalAnswers General Ledger files

    Parameter:
    -----------
    ledger : Ledger instance

    """
    null_account = '-x-'
    report_type_indicator = '++++++'

    def __init__(self, ledger):
        self.ledger = ledger
        self.filter = Filter(list(ledger.data.keys()))

    def reset(self):
        self.filter.reset()

    def detail(self, sort_by='actual,account,date', show_table=True, show_plot=True, sort_reverse=False, csv=False, cols_to_show='all'):
        """
        Look at detail in a svticular account with various filters and options.

        Parameters:
        ------------
        sort_by : list or csv-str
            columns to sort by
        sort_reverse : bool
            reverse sorting
        csv:  save the table as a csv file <True/False/'str'>
            if supplied,  uses 'str' as filename, if True uses default

        """
        if isinstance(sort_by, str):
            sort_by = sort_by.split(',')
        if cols_to_show == 'all':
            cols_to_show = list(self.ledger.columns_by_key.keys())

        total_lines = 0
        self.rows = {}
        self.subtotal = {'actual': 0.0, 'budget': 0.0, 'encumbrance': 0.0}
        self.cadence = {'daily': {}, 'monthly': {}, 'quarterly': {}, 'yearly': {}}
        ceys = {}
        for account in self.filter.account:
            if account in self.filter.exclude:
                continue
            if not isinstance(account, str):
                print(f"NOTICE - Accounts are usually str, {account} is {type(account)}")
                account = str(account)
            if account not in self.ledger.data.keys():
                continue
            for row in self.ledger.data[account]['entries']:
                for amtt in ['actual', 'budget', 'encumbrance']:
                    self.subtotal[amtt] += row[amtt]
                if not self.filter.check(row):
                    continue
                total_lines += 1
                # Get row
                key = []
                for sb in sort_by:
                    val = row[sb]
                    try:
                        val = int(float(val) * 100.0)
                    except (ValueError, TypeError, KeyError):
                        pass
                    key.append(val)
                key.append(total_lines)  # to ensure unique
                key = tuple(key)
                self.rows[key] = copy(row)
                # Get cadences
                for cad in self.cadence.keys():
                    ceys[cad] = ut.cadence_keys(cad, row['date'])
                    self.cadence[cad].setdefault(ceys[cad], {'actual': 0.0, 'budget': 0.0, 'encumbrance': 0.0})
                    for amtt in ['actual', 'budget', 'encumbrance']:
                        self.cadence[cad][ceys[cad]][amtt] += row[amtt]
        if not len(self.rows):
            return 0.0
        header = [self.ledger.columns_by_key[x][0] for x in cols_to_show]
        table_data = []
        for key in sorted(self.rows.keys(), reverse=sort_reverse):
            row = []
            for this_key in cols_to_show:
                if this_key == 'date':
                    row.append(self.rows[key][this_key].strftime('%Y-%m-%d'))
                else:
                    row.append(self.rows[key][this_key])
            table_data.append(row)
        if csv:
            ul.write_to_csv(csv, table_data, header)
        if show_table:
            print(tabulate(table_data, headers=header, floatfmt='.2f'))
            print(f"\nSub-total:  actual: {self.subtotal['actual']:.2f}, budget: {self.subtotal['budget']:.2f}, encumbrance: {self.subtotal['encumbrance']:.2f}")
        if show_plot:
            pl.cadences(self.cadence)
        return self.subtotal
