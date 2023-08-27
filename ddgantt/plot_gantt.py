"""
Creates a simple Gantt chart
Adapted from https://bitbucket.org/DBrent/phd/src/1d1c5444d2ba2ee3918e0dfd5e886eaeeee49eec/visualisation/plot_gantt.py  # noqa
BHC 2014

Adapted by ddeboer 6/Feb/2015
Re-adapted 2023 August 26
"""
import datetime
import matplotlib.pyplot as plt
from copy import copy
import matplotlib.dates
import numpy as np


def plotGantt(dates, labels, plotpars, extrema):
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
    """
    # Initialise plot
    fig1 = plt.figure(figsize=(9, 8), tight_layout=True)
    ax1 = fig1.add_subplot(111)
    datemin, datemax = matplotlib.dates.date2num(extrema.min), matplotlib.dates.date2num(extrema.max)
    deltadate = datemax - datemin
    ax1.axis(xmin=matplotlib.dates.date2num(extrema.min)-deltadate/10.0, xmax=matplotlib.dates.date2num(extrema.max)+deltadate/10.0)
    step = 0.5
    ymin = step
    ymax = len(labels) * step

    # Plot the data
    for i, dtlim in enumerate(dates):
        pp = plotpars[i]
        start = matplotlib.dates.date2num(dtlim[0])
        if dtlim[1] is None:  # Milestone
            plt.plot(start, i * step + ymin, pp.marker, color=pp.color, markersize=8)
        else:
            stop = matplotlib.dates.date2num(dtlim[1])
            plt.barh(i * step + ymin, stop - start, left=start, height=0.3,
                     align='center', color=pp.color, alpha=0.75)

    # Format the y-axis
    pos = np.arange(ymin, ymax + step / 2.0, step)  # add the step/2.0 to get that last value
    locsy, labelsy = plt.yticks(pos, labels)
    plt.setp(labelsy, fontsize=14)
    plt.grid(color='g', linestyle=':')

    # Plot current time
    now = datetime.datetime.now()
    if now >= extrema.min and now <= extrema.max:
        now_date = matplotlib.dates.date2num(now)
        plt.plot([now_date, now_date], [ymin - step, ymax + step], 'k--')

    ax1.xaxis_date()  # Tell matplotlib that these are dates...
    rule = matplotlib.dates.rrulewrapper(matplotlib.dates.MONTHLY, interval=1)
    loc = matplotlib.dates.RRuleLocator(rule)
    formatter = matplotlib.dates.DateFormatter("%b '%y")
    ax1.xaxis.set_major_locator(loc)
    ax1.xaxis.set_major_formatter(formatter)
    labelsx = ax1.get_xticklabels()
    plt.setp(labelsx, rotation=30, fontsize=12)

    # Finish up
    ax1.invert_yaxis()
    ax1.axis(ymin=ymax + (step - 0.01), ymax=ymin - (step - 0.01))
    fig1.autofmt_xdate()
    plt.tight_layout()