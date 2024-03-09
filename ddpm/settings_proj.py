import datetime


COLOR_PALETTE = [
    (0.12156862745098039, 0.4666666666666667, 0.7058823529411765, 1.0),
    (1.0, 0.4980392156862745, 0.054901960784313725, 1.0),
    (0.17254901960784313, 0.6274509803921569, 0.17254901960784313, 1.0),
    (0.8392156862745098, 0.15294117647058825, 0.1568627450980392, 1.0),
    (0.5803921568627451, 0.403921568627451, 0.7411764705882353, 1.0),
    (0.5490196078431373, 0.33725490196078434, 0.29411764705882354, 1.0)
        ]

DATE_FIELDS = ['date', 'begins', 'ends', 'updated', 'duration', 'timezone', 'lag']
LIST_FIELDS = ['note', 'predecessors', 'groups', 'reference']
PAST = datetime.datetime(year=2000, month=1, day=1)
FUTURE = datetime.datetime(year=2050, month=12, day=31)
STATUS_COLOR = {
    'complete': COLOR_PALETTE[2],
    'late': 'r',
    'other': 'k',
    'none': 'k',
    'moved': COLOR_PALETTE[1],
    'removed': COLOR_PALETTE[4]
}

BANNER_COLOR = 'steelblue'

# These are used in plot_proj.py and project.py "chart" 
CHART_DEFAULTS = {
    'colinear_delimiter': '|',
    'weekends': True,
    'months': True,
    'grid': True,
    'interval': None,
    'set_time_axis': False,
    'figsize': (12, 8),
    'savefig': False,
    'make_pretty': False
}