import matplotlib.pyplot as plt
import numpy as np


def chart(x, y, label, norm=1.0, width=0.65,  xlabel=None, ylabel=None):
    ind = list(range(len(x)))
    if isinstance(label, str):
        if len(x) != len(y):
            print("Dimensions wrong for bar chart.")
            return
        label = [label]
        plty = [np.array(y)]
    else:
        if len(y) != len(label) or len(x) != len(y[0]):
            print("Dimensions wrong for stacked bar chart.")
            return
        plty = []
        for this_group in y:
            plty.append(np.array(this_group) / norm)
    sumy = np.zeros(len(x))

    for this_label, this_plot in zip(label, plty):
        plt.bar(ind, this_plot, width, label=this_label, bottom=sumy)
        sumy += this_plot

    if xlabel is not None:
        plt.xlabel(xlabel)
    if ylabel is not None:
        plt.ylabel(ylabel)
    plt.xticks(ind, x)

def cadences(cadences, amounts):
    plt.figure(f"Cadences: {', '.join(amounts)}")
    for this_cadence in ['yearly', 'quarterly', 'monthly', 'daily']:
        ordered_keys = sorted(cadences[this_cadence].keys())
        ordered_amounts = []
        for key in ordered_keys:
            this_amt = 0.0
            for amtt in amounts:
                if amtt in cadences[this_cadence][key]:
                    this_amt += cadences[this_cadence][key][amtt]
            ordered_amounts.append(this_amt)
        if this_cadence == 'daily':
            plt.fill_between(ordered_keys, ordered_amounts)
            plt.plot(ordered_keys, ordered_amounts, 'k', label=this_cadence)
        else:
            plt.fill_between(ordered_keys, ordered_amounts, label=this_cadence)
    plt.legend()

def cumulative(cumulative, amounts):
    plt.figure(f"Cumulative: {', '.join(amounts)}")
    ordered_amounts = []
    ordered_smooth = []
    for i in range(len(cumulative['t'])):
        this_amt = 0.0
        this_sm = 0.0
        for amtt in amounts:
            if amtt in cumulative:
                this_amt += cumulative[amtt][i]
                this_sm += cumulative[f"smooth_{amtt}"][i]
        ordered_amounts.append(this_amt)
        ordered_smooth.append(this_sm)
    plt.fill_between(cumulative['t'], ordered_amounts)
    plt.plot(cumulative['t'], ordered_amounts, 'k')
    plt.plot(cumulative['t'], ordered_smooth, 'b', lw=2)