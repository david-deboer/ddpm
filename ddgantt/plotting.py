"""
Creates a simple Gantt chart
Adapted from https://bitbucket.org/DBrent/phd/src/1d1c5444d2ba2ee3918e0dfd5e886eaeeee49eec/visualisation/plot_gantt.py  # noqa
BHC 2014

Adapted by ddeboer 6/Feb/2015
Re-adapted 2023 August 26
"""
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates
import numpy as np
from ddgantt.gantt_util import color_palette


def date_ticks(interval, ddate):
    interval_mmap = {1:1, 2:2, 3:3, 4:3, 5:6, 7:6, 8:6, 9:12, 10:12, 11:12}
    dyr = ddate / 365.0
    itvmapper = matplotlib.dates.MONTHLY
    if interval is not None:
        try:
            interval = float(interval)
        except ValueError:
            if interval.endswith('d'):
                itvmapper = matplotlib.dates.DAILY
                interval = float(interval.strip('d'))
            elif interval.endswith('m'):
                interval = float(interval.strip('m'))
            else:
                raise ValueError(f"Interval must be float[d/m], you provided {interval}")
    else:
        if ddate > 300:
            interval = interval_mmap[int(np.ceil(dyr * dyr / 6.0))]
            fmttr = "%b '%y"
        else:
            itvmapper = matplotlib.dates.DAILY
            if ddate > 30:
                interval = 7
            else:
                interval = 1
            fmttr = "(%a) %b/%d"
    return itvmapper, interval, fmttr


def assign_yvals_labels(ykeys, labels):
    """
    Assigned a yvalue to all (colinear thing...)
    """
    step = 0.5
    ymin = step
    yvals = []
    fnd_keys = {}
    ctr = 0
    yticks = []
    ylabels = []
    cmap = {}
    for i, ykey in enumerate(ykeys):
        if ykey not in fnd_keys:
            ylabels.append(labels[i])
            yval = ymin + ctr * step
            yticks.append(yval)
            cmap[ykey] = ctr
            ctr += 1
            yvals.append(yval)
            fnd_keys[ykey] = yval
        else:
            yvals.append(fnd_keys[ykey])
            ylabels[cmap[ykey]] += '|' + labels[i]
        ylabels[cmap[ykey]] = ylabels[cmap[ykey]].strip('| ')
    return yvals, yticks, ylabels


def gantt_chart(dates, labels, plotpars, ykeys, extrema, **kwargs):
    """
    This will plot a gantt chart of items (ylabels) and dates.  If included, it will plot percent
    complete for tasks and color code for milestones (note, if included, it must have a status_codes
    entry for every label)  If included, it will connect predecessors (note, if included, it also
    must have an entry for every ylabel) other_labels prints another label by the entry (to right on
    plot), it also must have an entry for every ylabel

    Parameters
    ----------
    dates : list of lists -- each individual is a datetime pair (or end is None)
    labels : labels for dates
    markers : colors for entry
    extrema : 2 element list of min/max datetimes
    kwargs : interval, grid
    """
    # Initialise plot
    fig1 = plt.figure(figsize=(12, 8), tight_layout=True)
    ax1 = fig1.add_subplot(111)
    datemin, datemax = matplotlib.dates.date2num(extrema.min), matplotlib.dates.date2num(extrema.max)
    deltadate = datemax - datemin
    ax1.axis(xmin=matplotlib.dates.date2num(extrema.min)-deltadate/10.0, xmax=matplotlib.dates.date2num(extrema.max)+deltadate/10.0)
    yvals, yticks, ylabels = assign_yvals_labels(ykeys, labels)
    step = yticks[1] - yticks[0]

    # Plot the data
    for i, dtlim in enumerate(dates):
        pp = plotpars[i]
        start = matplotlib.dates.date2num(dtlim[0])
        if dtlim[1] is None:  # Milestone
            plt.plot(start, yvals[i], pp.marker, color=pp.color, markersize=8)
        else:
            stop = matplotlib.dates.date2num(dtlim[1])
            plt.barh(yvals[i],  stop - start, left=start, height=0.3, align='center', color=pp.color, alpha=0.75)
            if isinstance(pp.status, (float, int)):
                plt.barh(yvals[i], pp.status*(stop - start)/100.0, left=start, height=0.1, align='center', color='k', alpha=0.75)

    # Format the y-axis
    locsy, labelsy = plt.yticks(yticks, ylabels)
    plt.setp(labelsy, fontsize=14)
    if 'grid' in kwargs and not kwargs['grid']:
        pass
    else:
        plt.grid(color='0.6', linestyle=':')

    # Plot current time
    now = datetime.datetime.now()
    if now >= extrema.min and now <= extrema.max:
        now_date = matplotlib.dates.date2num(now)
        plt.plot([now_date, now_date], [yticks[0]-step, yticks[-1]+step], '--', color=color_palette[3])
    if int(deltadate) > 400:  # plot year markers
        yr1 = extrema.min.year
        yr2 = extrema.max.year
        if deltadate > 2.5*365 and extrema.max.month > 8:
            yr2 += 1
        for yr in range(yr1, yr2+1):
            this_yr = datetime.datetime(year=yr, month=1, day=1)
            plt.plot([this_yr, this_yr], [yticks[0]-step, yticks[-1]+step], 'k:')
    ax1.xaxis_date()  # Tell matplotlib that these are dates...
    interval = None if 'interval' not in kwargs else kwargs['interval']
    itvmapper, interval, fmttr = date_ticks(interval, deltadate)
    rule = matplotlib.dates.rrulewrapper(itvmapper, interval=interval)
    loc = matplotlib.dates.RRuleLocator(rule)
    formatter = matplotlib.dates.DateFormatter(fmttr)
    ax1.xaxis.set_major_locator(loc)
    ax1.xaxis.set_major_formatter(formatter)
    labelsx = ax1.get_xticklabels()
    plt.setp(labelsx, rotation=30, fontsize=12)

    # Finish up
    ax1.invert_yaxis()
    ax1.axis(ymin=yticks[-1] + (step - 0.01), ymax=yticks[0] - (step - 0.01))
    fig1.autofmt_xdate()
    plt.tight_layout()

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