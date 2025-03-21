"""
Creates a simple Gantt chart
Adapted from https://bitbucket.org/DBrent/phd/src/1d1c5444d2ba2ee3918e0dfd5e886eaeeee49eec/visualisation/plot_gantt.py  # noqa
BHC 2014
# https://towardsdatascience.com/5-steps-to-build-beautiful-bar-charts-with-python-3691d434117a
https://www.geeksforgeeks.org/style-plots-using-matplotlib/
Adapted by ddeboer 6/Feb/2015
Re-adapted 2023 August 26
Re-re-adapted 2023 October 23 - made into class
"""
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates
import numpy as np
from . import settings_proj as settings
from . import utils_time as ut
from os import path


class StateVariable:
    def __init__(self, kwargs={}, defaults={}):
        self.update(kwargs, defaults)

    def __repr__(self):
        from tabulate import tabulate
        table = []
        for a in dir(self):
            if a.startswith('__') or a == 'update':
                continue
            else:
                val = str(getattr(self, a))
                if len(val) > 50:
                    val = val[:50] + '...'
                table.append([a, val])
        return tabulate(table, headers=['Variable', 'Value'])

    def update(self, kwargs={}, defaults={}):
        """
        Process all of the keywords with provided defaults.
        """
        # Copy over defaults if not present
        for key, val in defaults.items():
            if key not in kwargs:
                kwargs[key] = val

        for key, value in kwargs.items():
            setattr(self, key, value)


class Gantt:
    def __init__(self, name=None):
        self.name = name
        self.sv = StateVariable()

    def setup(self, dates, info, labels, ykeys, extrema, timezone=None):
        """
        Parameters
        ----------
        dates : list
            each entry is a datetime pair (or end is None)
        info : list
            list of Namespaces containing the data for the chart
        labels : list
            extra labels for entries
        ykeys : list
            entry keys contained within the plot
        extrema : Namespace
            min/max datetimes
        """
        self.dates = dates
        self.info = info
        self.labels = labels
        self.ykeys = ykeys
        self.extrema = extrema
        self.datemin, self.datemax = matplotlib.dates.date2num(extrema.min), matplotlib.dates.date2num(extrema.max)
        self.deltadate = self.datemax - self.datemin
        self.timezone = timezone

    def plot_weekends(self, ax, color='lightcyan'):
        """
        Include weekend on the plot.
        
        Parameter
        ---------
        color : str
            color to use for the weekends
        """
        first_sat = self.extrema.min - datetime.timedelta(days=6)
        while first_sat.weekday() != 5:
            first_sat += datetime.timedelta(days=1)
        ybound = 1.1 * len(self.ykeys)
        this_date = datetime.datetime(year=first_sat.year, month=first_sat.month, day=first_sat.day).replace(tzinfo=self.timezone)
        while this_date < self.extrema.max:
            ax.fill_between([this_date, this_date + datetime.timedelta(days=2)], [ybound, ybound], -10, color=color)
            this_date += datetime.timedelta(days=7)

    def plot_months(self, ax, color='0.7'):
        ybound = 1.1 * len(self.ykeys)
        if self.extrema.min.day < 10:
            first_day = datetime.datetime(year=self.extrema.min.year, month=self.extrema.min.month, day=1).replace(tzinfo=self.timezone)
            ax.plot([first_day, first_day], [-10, ybound], '--', lw=2, color=color)
        this_day = (ut.last_day_of_month(self.extrema.min, return_datetime=True) + datetime.timedelta(days=1)).replace(tzinfo=self.timezone)
        while this_day < self.extrema.max:
            ax.plot([this_day, this_day], [-10, ybound], '--', lw=2, color=color)
            this_day = (ut.last_day_of_month(this_day, return_datetime=True) + datetime.timedelta(days=1)).replace(tzinfo=self.timezone)
        if self.extrema.max.day > 20:
            this_day = (ut.last_day_of_month(self.extrema.max, return_datetime=True) + datetime.timedelta(days=1)).replace(tzinfo=self.timezone)
            ax.plot([this_day, this_day], [-10, ybound], '--', lw=2, color=color)

    def assign_yvals_labels(self, colinear_delimiter='\n'):
        """
        Assigned a yvalue to all ykeys (colinear thing...)
        """
        step = 0.5
        ymin = step
        self.yvals = []
        fnd_keys = {}
        ctr = 0
        self.yticks = []
        self.ylabels = []
        cmap = {}
        for i, ykey in enumerate(self.ykeys):
            if ykey not in fnd_keys:
                self.ylabels.append(self.labels[i])
                yval = ymin + ctr * step
                self.yticks.append(yval)
                cmap[ykey] = ctr
                ctr += 1
                self.yvals.append(yval)
                fnd_keys[ykey] = yval
            else:
                self.yvals.append(fnd_keys[ykey])
                self.ylabels[cmap[ykey]] += colinear_delimiter + self.labels[i]
            self.ylabels[cmap[ykey]] = self.ylabels[cmap[ykey]].strip(colinear_delimiter + ' ')

    def date_ticks(self, interval=None):
        interval_mmap = {1:1, 2:2, 3:3, 4:3, 5:6, 7:6, 8:6, 9:12, 10:12, 11:12, 12:12, 13:12}
        dyr = self.deltadate / 365.0
        self.itvmapper = matplotlib.dates.MONTHLY
        if interval is not None:
            try:
                interval = int(interval)
            except ValueError:
                if interval.endswith('d'):
                    self.itvmapper = matplotlib.dates.DAILY
                    interval = int(interval.strip('d'))
                    self.fmttr = "(%a) %b/%d"
                elif interval.endswith('m'):
                    interval = int(interval.strip('m'))
                    self.fmttr = "%b '%y"
                else:
                    raise ValueError(f"Interval must be float[d/m], you provided {interval}")
        else:
            if self.deltadate > 300:
                interval = interval_mmap[int(np.ceil(dyr * dyr / 5.0))]
                self.fmttr = "%b '%y"
            else:
                self.itvmapper = matplotlib.dates.DAILY
                if self.deltadate > 30:
                    interval = 7
                else:
                    interval = 1
                self.fmttr = "(%a) %b/%d"
        self.interval = interval

    def chart(self, **kwargs):
        """
        This will plot a gantt chart of items (ylabels) and dates.  If included, it will plot percent
        complete for tasks and color code for milestones (note, if included, it must have a status_codes
        entry for every label)  If included, it will connect predecessors (note, if included, it also
        must have an entry for every ylabel) other_labels prints another label by the entry (to right on
        plot), it also must have an entry for every ylabel

        Parameters
        ----------

        """
        self.sv.update(kwargs, settings.CHART_DEFAULTS)
        if self.sv.style not in plt.style.available:
            self.sv.style = path.join(settings.STYLE_DIR, f"{self.sv.style}.mplstyle")
        if self.sv.figsize == 'auto':
            print("DO SOMETHING HERE")

        # Initialise plot
        with plt.style.context(self.sv.style):
            self.fig_gantt, self.ax_gantt = plt.subplots(ncols=1, nrows=1, figsize=self.sv.figsize,  layout='constrained')
            self.ax_gantt.axis(xmin=matplotlib.dates.date2num(self.extrema.min)-self.deltadate/10.0,
                                xmax=matplotlib.dates.date2num(self.extrema.max)+self.deltadate/10.0)
            self.assign_yvals_labels(self.sv.colinear_delimiter)
            try:
                step = self.yticks[1] - self.yticks[0]
            except IndexError:
                step = 0.1

            if self.sv.weekends:
                self.plot_weekends(self.ax_gantt)
            if self.sv.months:
                self.plot_months(self.ax_gantt)

            # Plot the data
            for i, dtlim in enumerate(self.dates):
                info = self.info[i]
                start = matplotlib.dates.date2num(dtlim[0])
                if dtlim[1] is None:  # Milestone
                    self.ax_gantt.plot(start, self.yvals[i], info.marker, color=info.color, markersize=8)
                else:
                    stop = matplotlib.dates.date2num(dtlim[1])
                    self.ax_gantt.barh(self.yvals[i],  stop - start, left=start, height=0.3, align='center', color=info.color, alpha=0.75)
                    try:
                        if isinstance(info.status, (float, int)):
                            self.ax_gantt.barh(self.yvals[i], info.status*(stop - start)/100.0, left=start, height=0.1, align='center', color='k', alpha=0.75)
                    except AttributeError:
                        continue

            # Format the y-axis
            self.ax_gantt.set_yticks(self.yticks, labels=self.ylabels, fontsize=14)

            # Plot current time
            now = datetime.datetime.now().astimezone(self.timezone)
            if now >= self.extrema.min and now <= self.extrema.max:
                now_num = matplotlib.dates.date2num(now)
                self.ax_gantt.plot([now_num, now_num], [self.yticks[0]-step, self.yticks[-1]+step], '--', color=settings.COLOR_PALETTE[3])
            if int(self.deltadate) > 400:  # plot year markers
                yr1 = self.extrema.min.year
                yr2 = self.extrema.max.year
                if self.deltadate > 2.5*365 and self.extrema.max.month > 8:
                    yr2 += 1
                for yr in range(yr1, yr2+1):
                    this_yr = datetime.datetime(year=yr, month=1, day=1)
                    self.ax_gantt.plot([this_yr, this_yr], [self.yticks[0]-step, self.yticks[-1]+step], 'k:')
            self.ax_gantt.xaxis_date(tz=self.timezone)  # Tell matplotlib that these are dates...
            if self.sv.set_time_axis:
                self.date_ticks(self.sv.interval)
                rule = matplotlib.dates.rrulewrapper(self.itvmapper, interval=self.interval)
                loc = matplotlib.dates.RRuleLocator(rule, tz=self.timezone)
                formatter = matplotlib.dates.DateFormatter(self.fmttr, tz=self.timezone)
                self.ax_gantt.xaxis.set_major_locator(loc)
                self.ax_gantt.xaxis.set_major_formatter(formatter)
            self.ax_gantt.set_xticks(self.ax_gantt.get_xticks(), self.ax_gantt.get_xticklabels(), rotation=30, fontsize=12, ha='right')

            # Finish up
            self.ax_gantt.invert_yaxis()
            self.ax_gantt.axis(ymin=self.yticks[-1] + (step - 0.01), ymax=self.yticks[0] - (step - 0.01))

            # Add in banner line and rectangle on top
            if self.sv.banner is not None:
                self.ax_gantt.plot([0.05, 1.0], [.98, .98], transform=self.fig_gantt.transFigure, clip_on=False, color=self.sv.banner, linewidth=.6)
                self.ax_gantt.add_patch(plt.Rectangle((0.05,.98), 0.04, -0.02, facecolor=self.sv.banner, transform=self.fig_gantt.transFigure, clip_on=False, linewidth = 0))

                # Add in title and subtitle
                self.ax_gantt.text(x=0.05, y=.93, s="Text 1", transform=self.fig_gantt.transFigure, ha='left', fontsize=14, weight='bold', alpha=.8)
                self.ax_gantt.text(x=0.05, y=.90, s="Text 2", transform=self.fig_gantt.transFigure, ha='left', fontsize=12, alpha=.8)

            # Adjust the margins around the plot area
            #self.ax_gantt.subplots_adjust(left=None, bottom=0.2, right=None, top=0.95, wspace=None, hspace=None)

            if self.sv.savefig:
                if isinstance(self.sv.savefig, str):
                    plt.savefig(self.sv.savefig)
                else:
                    plt.savefig('bar_chart.png')

def cumulative_graph(dates, values, norm):
    datemin, datemax = matplotlib.dates.date2num(dates[0]), matplotlib.dates.date2num(dates[-1])
    cx_dat = [matplotlib.dates.date2num(_x) for _x in dates]
    cy_dat = np.array(values) / norm
    fig2 = plt.figure('cdf')
    ax2 = fig2.add_subplot(111)
    ax2.axis(xmin=datemin, xmax=datemax, ymin=0.0, ymax=1.0)
    plt.plot(cx_dat, cy_dat)
    plt.ylabel('Fraction Completed')
    plt.grid()
    ax2.xaxis_date()  # Tell matplotlib that these are dates...
    rule = matplotlib.dates.rrulewrapper(matplotlib.dates.MONTHLY, interval=1)
    loc = matplotlib.dates.RRuleLocator(rule)
    formatter = matplotlib.dates.DateFormatter("%b '%y")
    ax2.xaxis.set_major_locator(loc)
    ax2.xaxis.set_major_formatter(formatter)
    labelsx = ax2.get_xticklabels()
    plt.setp(labelsx, rotation=30, fontsize=12)