
from copy import copy
from tabulate import tabulate
from . import utils_ledger as ul
from . import utils_time as ut
from . import plots_ledger as plots
from dateutil.parser import parse
from datetime import datetime, timedelta


class Filter:
    def __init__(self, ledger_accounts, dates, amounts):
        """
        Parameter
        ---------
        ledger_accounts : list
            Full list of ledger keys (accounts)
        dates : list
            List of element types intrepreted as dates
        amounts : list
            List of element types interpreted as amounts

        Attributes
        ----------
        same as above
        absval : dict
            Flag to use absolute value or not per amount_type
        amount : dict
            'type': amount_type keys, 'low'/'high': low/high values per amount_type key
        date : dict
            'type': date_type keys, 'start'/'stop': start/end values per date_type

        """
        self.ledger_accounts = ledger_accounts
        self.absval = {}
        self.amount = {'type': amounts, 'low': {}, 'high': {}}
        self.date = {'type': dates, 'start': {}, 'stop': {}}
        self.reset()

    def reset(self):
        self.set_account('account', 'all')
        self.set_account('exclude', None)
        for amtt in self.amount['type']:
            self.set_amount(amtt, 'all')
        for datt in self.date['type']:
            self.set_date(datt, 'all')
        self.other = {}

    def set(self, **kwargs):
        """
        You can call set_X directly, but generally use this general set command X=Y
        """
        for key, value in kwargs.items():
            if key in self.amount['type']:
                self.set_amount(key, value)
            elif key in self.date['type']:
                self.set_date(key, value)
            elif key in ['account', 'exclude']:
                self.set_account(key, value)
            else:
                self.other[key] = value
            
    def set_account(self ,key, val):
        if isinstance(val, str):
            if val.lower() == 'all':
                setattr(self, key, self.ledger_accounts)
            elif val.lower() == 'none':
                setattr(self, key, [])
            else:
                setattr(self, key, val.split(','))
        elif isinstance(val, list):
            setattr(self, key, [str(x) for x in val])
        elif val is None:
            setattr(self, key, [])

    def set_date(self, key, val):
        if key not in self.date['type']:
            print(f"{key} not an allowed date type")
            return
        val = 'all' if val is None else val
        self.date['start'][key] = datetime(year=2000, month=1, day=1).astimezone()
        self.date['stop'][key] = datetime(year=2100, month=12, day=31).astimezone()
        if val == 'all':
            return
        try:
            val = parse(val)
        except parse.ParserError:
            pass
        if isinstance(val, datetime):
            self.date['start'][key] = datetime(year=val.year, month=val.month, day=val.day, hour=0, minute=0, second=0).astimezone()
            self.date['stop'][key] = datetime(year=val.year, month=val.month, day=val.day, hour=23, minute=59, second=59).astimezone()
        else:
            self.date['start'][key], self.date['stop'][key] = [parse(x).astimezone() for x in val.split('_')]

    def set_amount(self, key, val):
        """

        """
        if key not in self.amount['type']:
            print(f"{key} not an allowed amount type")
            return
        self.absval[key] = False
        self.amount['low'][key] = -1E15
        self.amount['high'][key] = 1E15
        val = 'all' if val is None else val
        if val == 'all':
            return
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
                self.amount['high'][key] = float(val.replace(',', '').replace('$', '').replace('<', ''))
            elif val.startswith('>'):
                self.amount['low'][key] = float(val.replace(',', '').replace('$', '').replace('>', ''))
            elif '_' in val:
                self.amount['low'][key], self.amount['hight'][key] = [float(x.replace(',', '').replace('$', '')) for x in val.split('_')]
        else:  # Within a dollar
            self.amount['low'][key] = val - 1.0
            self.amount['high'][key] = val + 1.0

    def allow(self, data):
        """
        This currently only does "OR", i.e. if any fail it fails

        """
        for this_date_key in self.date['type']:
            if data[this_date_key] < self.date['start'][this_date_key] or data[this_date_key] > self.date['stop'][this_date_key]:
                return False
        for this_amt_key in self.amount['type']:
            this_one = abs(data[this_amt_key]) if self.absval[this_amt_key] else data[this_amt_key]
            if this_one < self.amount['low'][this_amt_key] or this_one > self.amount['high'][this_amt_key]:
                return False
        for key, val in self.other.items():
            if isinstance(val, list) and data[key] not in val:
                return False
            elif data[key] != val:
                return False
        return True

class Audit():
    """
    Look at Ledger files
    """

    def __init__(self, ledger, chart_amounts=None):
        """
        Parameters
        ----------
        ledger : Ledger instance
        chart_amounts : list or None
            List of amount types to use as default for plots and projections, can override in the call

        Attributes
        ----------
        ledger : Ledger instance
        filter : Filter instance
        self.chart_amounts : list or None
            See Parameters
        smooth : None

        """
        self.ledger = ledger
        self.filter = Filter(ledger_accounts=list(ledger.data.keys()),
                             dates=list(ledger.date_types),
                             amounts=list(ledger.amount_types))
        self.chart_amounts = chart_amounts
        self.smooth = None

    def in_fill_cadence_cumulative(self):
        """
        In-fill cadences that don't have data with a 0.0 and make the cumulative data on daily basis.

        """
        self.cumulative = {}
        now = datetime.now().astimezone().replace(hour=23, minute=59, second=0, microsecond=0)
        for this_cadence in ['daily', 'monthly', 'quarterly', 'yearly']:
            ordered_keys = sorted(self.cadence[this_cadence].keys())
            if not len(ordered_keys):
                continue
            this_time = copy(ordered_keys[0])
            if this_cadence == 'daily':
                self.cumulative[this_time] = {}
                for amtt in self.ledger.amount_types:
                    self.cumulative[this_time][amtt] = self.cadence['daily'][this_time][amtt]
            while this_time < ordered_keys[-1]:
                prev_time = copy(this_time)
                this_time = ut.cadence_keys(this_cadence, this_time + timedelta(days=1))
                if this_time > now:
                    this_time = now
                if this_time in ordered_keys:
                    pass
                else:
                    self.cadence[this_cadence][this_time] = {}
                    for amtt in self.ledger.amount_types:
                        self.cadence[this_cadence][this_time][amtt] = 0.0
                if this_cadence == 'daily':
                    self.cumulative[this_time] = {}
                    for amtt in self.ledger.amount_types:
                        self.cumulative[this_time][amtt] = self.cumulative[prev_time][amtt] + self.cadence['daily'][this_time][amtt]
        self.smooth_cumulative_rates()

    def _get_sort_key(self, row, sort_by, use_absval):
        key = []
        for sb in sort_by:
            val = row[sb]
            try:
                val = int(float(val) * 100.0)
                if use_absval:
                    val = abs(val)
            except (ValueError, TypeError):
                pass
            key.append(val)
        key.append(self.total_lines)  # to ensure unique
        return tuple(key)

    def detail(self, sort_by='account,date', sort_reverse=False, cols_to_show='all', csv=False):
        """
        Look at detail in a svticular account with various filters and options.

        Parameters:
        ------------
        sort_by : list or csv-str
            columns to sort by
        sort_reverse : bool
            reverse sorting
        cols_to_show : str or list
            column keys used
        csv:  save the table as a csv file <True/False/'str'>
            if supplied,  uses 'str' as filename, if True uses default

        Attributes
        ----------
        rows : dict
        subtotal : dict
        cadence : dict
        header : list
        table_data : list

        """
        if isinstance(sort_by, list):
            sort_by = ','.join(sort_by)
        use_absval = True if '|' in sort_by else False  # All or none at this time.
        sort_by = sort_by.replace('|', '').split(',')
                
        if cols_to_show == 'all':
            cols_to_show = list(self.ledger.columns)
        elif isinstance(cols_to_show, str):
            cols_to_show = cols_to_show.split(',')

        self.total_lines = 0
        self.rows = {}
        self.subtotal = {}
        for amtt in self.ledger.amount_types:
            self.subtotal[amtt] = 0.0
        self.cadence = {'daily': {}, 'monthly': {}, 'quarterly': {}, 'yearly': {}}
        now = datetime.now().astimezone().replace(hour=23, minute=59, second=0, microsecond=0)
        for account in self.filter.account:
            if account in self.filter.exclude:
                continue
            if not isinstance(account, str):
                print(f"NOTICE - Accounts are usually str, {account} is {type(account)} - converting to str (?!?)")
                account = str(account)
            if account not in self.ledger.data.keys():
                continue
            for row in self.ledger.data[account]['entries']:
                if not self.filter.allow(row):
                    continue
                for amtt in self.ledger.amount_types:
                    self.subtotal[amtt] += row[amtt]
                self.total_lines += 1
                # Get row
                key = self._get_sort_key(row=row, sort_by=sort_by, use_absval=use_absval)
                self.rows[key] = copy(row)
                # Get cadences
                for cad in self.cadence.keys():
                    cey = ut.cadence_keys(cad, row['date'])  # Last minute of that cadence
                    if cey > now:
                        cey = now
                    if cey not in self.cadence[cad]:
                        self.cadence[cad][cey]= {}
                        for amtt in self.ledger.amount_types:
                            self.cadence[cad][cey][amtt] = 0.0
                    for amtt in self.ledger.amount_types:
                        self.cadence[cad][cey][amtt] += row[amtt]
        self.header = []
        for _x in cols_to_show:
            if _x in self.ledger.columns:
                self.header.append(self.ledger.columns[_x])
        self.table_data = []
        self.in_fill_cadence_cumulative()
        if not len(self.rows):
            return 
        for key in sorted(self.rows.keys(), reverse=sort_reverse):
            row = []
            for this_key in cols_to_show:
                if this_key in self.rows[key]:
                    if this_key in self.ledger.date_types:
                        row.append(self.rows[key][this_key].strftime('%Y-%m-%d'))
                    else:
                        row.append(self.rows[key][this_key])
            self.table_data.append(row)
        if csv:
            ul.write_to_csv(csv, self.table_data, self.header)

    def show_table(self):
        """
        Shows the detail table and subtotals

        """
        print()
        print(tabulate(self.table_data, headers=self.header, floatfmt='.2f'))
        print(f"\nSub-total:") 
        for amtt in self.ledger.amount_types:
            print(f"\t{amtt}:  {self.subtotal[amtt]:.2f}")

    def show_plots(self, amounts=None):
        """
        Plots the cadence and cumulative data.

        """
        amounts = ul.get_amount_list(amounts=amounts, amount_types=self.ledger.amount_types, chart_amounts=self.chart_amounts)
        plots.cadences(self.cadence, amounts=amounts)
        plots.cumulative(self.cumulative, amounts=amounts, smooth=self.smooth)

    def smooth_cumulative_rates(self, amounts=None, fs=1.0, cutoff=60.0, order=8):
        self.fs = fs
        self.cutoff = 1.0 / cutoff
        self.order = order
        self.smooth = {}
        self.diff = {}
        ordered_keys = sorted(self.cumulative.keys())
        for amtt in self.ledger.amount_types:
            ordered_amounts = []
            self.smooth[amtt] = 0.0
            for key in ordered_keys:
                this_amt = 0.0
                self.smooth[amtt] 
                for amtt in amounts:
                    if amtt in self.cumulative[key]:
                        this_amt += self.cumulative[key][amtt]
                ordered_amounts.append(this_amt)
            from numpy import diff, insert, mean
            self.smooth = ul.butter_lowpass_filter(ordered_amounts, self.cutoff, self.fs, self.order)
            self.diff = insert(diff(self.smooth), 0, 0.0)
            plots.plt.figure("DIFF")
            plots.plt.plot(ordered_keys, self.diff)
            ilo = int(0.15 * len(ordered_amounts))
            ihi = int(0.85 * len(ordered_amounts))
            mv = mean(self.diff[ilo:ihi])
            plots.plt.plot([ordered_keys[ilo], ordered_keys[ihi]], [mv, mv], lw=4)

