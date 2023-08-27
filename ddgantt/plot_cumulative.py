   
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np


def plotCumulative(dates, labels, plotpars, extrema):
    cx_dat = None
    cy_dat = None
    cdf_tot = None
    cdf_tot = len(labels)
    datemin, datemax = matplotlib.dates.date2num(extrema.min), matplotlib.dates.date2num(extrema.max)
    print(extrema)
    cx_dat = np.arange(datemin, datemax, 1.0)
    cy_dat = []
    for xd in cx_dat:
        ctr = 0.0
        for i in range(len(labels)):
            this_date = matplotlib.dates.date2num(dates[i][0])
            if xd > this_date and plotpars.status == 'complete':
                ctr += 1.0
        cy_dat.append(ctr)  # /len(ylabels))
    cy_dat = np.array(cy_dat)
    fig2 = plt.figure('cdf')
    ax2 = fig2.add_subplot(111)
    ax2.axis(xmin=datemin, xmax=datemax, ymin=0.0, ymax=1.0)
    plt.plot(cx_dat, cy_dat / cdf_tot)
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
    return_info = {'cdf_x': cx_dat, 'cdf_y': cy_dat, 'cdf_tot': cdf_tot}
    return return_info
