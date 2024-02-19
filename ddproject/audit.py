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
            filter_by_amt:  only choose for values set by filter_by_amt e.g. '>|1.0' <str, None>
                            allowed prefixes: {'<', '>', '=', '|'}  ('|' for absolute value)
                            use '_' for between amounts
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

    def make_time_data(self, tag, color=None, intervals={'yearly': True, 'monthly': True, 'daily': True}):
        """
        Makes the data for plots of transactions

        Parameters:
        ------------
        tag : str 
            tag for time data
        color : str or None
            if specified color for tag
        intervals : dict
            intervals to use and infill settings
        """
        time, amt = [], []
        for i, k in enumerate(sorted(self.account_dict.keys(), reverse=False)):
            time.append(self.account_dict[k]['date'])
            amt.append(self.account_dict[k]['amount'])
        self.time_data[tag] = tdt.TimeData(time, amt, is_sorted=False)
        if len(time):
            self.time_data[tag] = tdt.TimeData(time, amt, is_sorted=False)
            self.time_data[tag].make_cumrate()
            for this_interval in intervals:
                self.time_data[tag].make_interval(this_interval, infill=intervals[this_interval])
            self.time_data[tag].color = color

    def total_accounts(self, accounts):
        print(f"Totaling {len(accounts)} for {self.using_amt}")
        tot = 0.0
        for c in accounts:
            for budget_type in self.using_amt:
                tot += self.data[c][budget_type]
        return tot

    def plot_various(self, groups=None, **options):
        """
            cumul_fig_name:  figure(cumul_fig_name) [CumulativeEntries]
            daily_fig_name:  figure(daily_fig_name) [Daily]
            rate_fig_name: figure(rate_fig_name) [Rate]
            rate_span:  time in days over which to computer rate [90]
            rate_smoothing:  time in days over which to smooth rate [2]
        """
        if groups is None:
            groups = list(self.time_data.keys())
        self.sv.plot.state(meta_state=options)
        self.rates = {}
        for grp in groups:
            self.plot_cumulative(grp)
            self.plot_rate(grp)
        for interval in ['yearly', 'monthly', 'daily']:
            self.plot_interval(interval, groups)

    def plot_cumulative(self, group, show_entries=True, **options):
        if not len(self.time_data[group].times):
            return
        self.sv.plot.state(meta_state=options)
        plt.figure(self.sv.plot.cumul_fig_name)
        if self.plot_title is not None:
            plt.title(self.plot_title)
        this_data = self.time_data[group]
        if show_entries:
            plt.plot(this_data.times, this_data.values, '_', color=this_data.color)
        plt.plot(this_data.times, this_data.cum,
                 color=this_data.color, label=group)
        plt.xlabel('Date')
        plt.ylabel('$')
        if self.sv.plot.add_time_legend:
            plt.legend()
        plt.savefig('cumulative.png')

    def plot_interval(self, interval, groups, **options):
        self.sv.plot.state(meta_state=options)
        plt.figure(interval)
        if self.plot_title is not None:
            plt.title(self.plot_title + ':' + interval)
        try:
            use_chart = len(getattr(self.time_data[groups[0]], interval).times) < 11
        except AttributeError:
            print(f"No {interval} to plot.")
            return
        # use_chart = interval in ['yearly', 'monthly']
        plot_type = 'chart' if use_chart else 'line'
        pltx = []
        plty = []
        pltc = []
        pltg = []
        for group in groups:
            if group == 'not_included':
                continue
            pltg.append(group)
            try:
                this_data = getattr(self.time_data[group], interval)
            except AttributeError:
                print(f"{group} does not have interval {interval}")
                continue
            if plot_type == 'chart':
                pltx.append( [x.strftime('%Y-%m-%d') for x in this_data.times] )
            else:
                pltx.append(this_data.times)
            plty.append(copy(this_data.values))
            pltc.append(copy(self.time_data[group].color))
        if plot_type == 'chart':
            ul.chart(pltx[0], plty, pltg, width=.75, chart_title=interval)
        else:
            for i in range(len(pltx)):
                plt.plot(pltx[i], plty[i], color=pltc[i], label=pltg[i])
        plt.xlabel('Date')
        plt.ylabel('$')
        if self.sv.plot.add_time_legend:
            plt.legend()
        plt.savefig(f'{interval}.png')

    def plot_rate(self, group, **options):
        if not len(self.time_data[group].times):
            return
        self.sv.plot.state(meta_state=options)
        plt.figure(self.sv.plot.rate_fig_name)
        if self.plot_title is not None:
            plt.title(self.plot_title)
        this_data = self.time_data[group]
        if 'dots' in self.sv.plot.meta.state and self.sv.plot.dots:
            norm_monthly = np.array(this_data.monthly.values) / 1000.0
            plt.plot(this_data.monthly.times, norm_monthly, 'o', color=this_data.color)
        ave_monthly = this_data.monthly.cum[-1] / len(this_data.monthly.cum)
        monspan = [this_data.monthly.times[0], this_data.monthly.times[-1]]
        plt.plot(this_data.times, this_data.rate,
                 color=this_data.color, label=group)
        plt.plot(monspan, [ave_monthly/1000.0, ave_monthly/1000.0], color=this_data.color)
        plt.xlabel('Date')
        plt.ylabel('k$/month')
        if self.sv.plot.add_time_legend:
            print(f"Average {group:15s}  {ul.print_money(ave_monthly, True):>12s}  $/month")
            plt.legend()
        plt.savefig('rate.png')
