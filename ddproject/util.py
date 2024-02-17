import matplotlib.pyplot as plt
import datetime
import requests
import csv
from copy import copy
from numpy import floor


color_palette = [
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
    'complete': color_palette[2],
    'late': 'r',
    'other': 'k',
    'none': 'k',
    'moved': color_palette[1],
    'removed': color_palette[4]
}


def months_to_timedelta(starts, duration_mo):
    starts = datetimedelta(starts)
    int_mo = int(floor(duration_mo))
    yr, mo = int_mo // 12, int_mo % 12
    dy = (duration_mo - int_mo) * 30.42
    new_month = starts.month + mo
    new_year = starts.year + yr
    new_day = starts.day + int(dy)

    if new_month > 12:
        new_month -= 12
        new_year += 1
    ends = datetime.datetime(year=new_year, month=new_month, day=new_day) - datetime.timedelta(days=1)
    duration = ends - starts
    return duration


def components_parameters(show=True):
    from . import components
    allcmp = {}
    for cmpnt, cls in components.components_dict().items():
        try:
            allcmp[cmpnt] = cls.parameters
        except AttributeError:
            pass
    if show:
        for cmpnt, clspar in allcmp.items():
            print(f"{cmpnt}: {', '.join(clspar)}")
    else:
        return allcmp


def pretty_duration(seconds):
    """
    Display a duration (given in seconds) in a more human-readable form.

    Parameters
    ----------
    seconds : float, int
        Number of seconds in the duration

    Return
    ------
    str
        Text of the duration.

    """
    years = seconds / (86400 * 365)  # approximately...
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 365:
        s = f"{years:.1f} years  ({days} days)"
    elif days > 30:
        s = f"{days} days"
    elif days > 3:
        s = f"{days} days {hours} hours"
    elif days > 1:
        s = f"{hours} hours"
    else:
        s = f"{hours} hours {minutes} minutes"
    return s

def load_sheet_from_url(url):
    """
    Load in a csv-sheet from a published googledoc

    Parameters
    ----------
    url : str
        url containing the published googledoc
    
    Return
    ------
    list
        list of strings containing the csv data
    """
    sheet_info = []
    try:
        xxx = requests.get(url)
    except Exception as e:
        print(f"Error reading {url}:  {e}")
        return
    csv_tab = b''
    for line in xxx:
        csv_tab += line
    _info = csv_tab.decode('utf-8').splitlines()
    for nn in csv.reader(_info):
        sheet_info.append(nn)
    return sheet_info

def quarters(dates):
    smo = dates[0].month
    if smo < 4:
        umo = 1
    elif smo < 7:
        umo = 4
    elif smo < 10:
        umo = 9
    else:
        umo = 10
    this_date = datetime.datetime(year=dates[0].year, month=umo, day=1)
    q = [this_date]
    while this_date < dates[-1]:
        ndt = this_date + datetime.timedelta(days=95)
        this_date = datetime.datetime(year=ndt.year, month=ndt.month, day=1)
        q.append(this_date)
    return(q)

def datedeltastr(val, fmt='%Y-%m-%d %H:%M'):
    if isinstance(val, datetime.datetime):
        return val.strftime(fmt)
    elif isinstance(val, datetime.timedelta):
        return f"{val.days + val.seconds / 86400:.2f}"
    else:
        return None

def get_timezone(hours=None, name=None):
    if hours is None:
        return copy(datetime.datetime.now().astimezone().tzinfo)
    if name is None:
        sgn = '+' if float(hours) >= 0.0 else '-'
        name = f"UTC{sgn}{float(hours):.0f}"
    return datetime.timezone(datetime.timedelta(hours=float(hours)), name)

def datetimedelta(date, key=None, fmt=['%Y-%m-%d', '%y/%m/%d', '%Y-%m-%d %H:%M'], timezone=None):
    """
    Returns
    -------
    A tz-aware datetime, a timedelta or a timezone
    """
    if key == 'timezone':
        name = None
        if isinstance(date, (list, tuple)):
            hr = date[0]
            name = str(date[1])
        else:
            hr = date
        return get_timezone(hours=hr, name=name)

    if date is None:
        return None
    if isinstance(date, str):
        if date.lower() == 'none' or not len(date.strip()):
            return None

    if key in ['duration', 'lag']:
        if isinstance(date, datetime.timedelta):
            return date
        try:
            return datetime.timedelta(days = float(date))
        except (TypeError, ValueError):
            return None

    if date == 'now':
        return datetime.datetime.now().astimezone(timezone)
    if isinstance(date, datetime.datetime):
        return date.replace(tzinfo=timezone)
    if isinstance(date, str):
        for this_fmt in fmt:
            try:
                dt = datetime.datetime.strptime(date, this_fmt)
                return dt.replace(tzinfo=timezone)
            except ValueError:
                pass
    raise ValueError(f"Invalid date format {type(date)} - {date}")

def complete2rgb(lag):
    s = 255.0
    bs = [[85.0, (255.0 / s, 190.0 / s, 50.0 / s)],
          [50.0, (220.0 / s, 110.0 / s, 110.0 / s)],
          [25.0, (125.0 / s, 110.0 / s, 150.0 / s)],
          [5.0, (55.0 / s, 0.0 / s, 250.0 / s)],
          [-5.0, (55.0 / s, 0.0 / s, 250.0 / s)],
          [-25.0, (0.0 / s, 200.0 / s, 0.0 / s)],
          [-85.0, (0.0 / s, 255.0 / s, 0.0 / s)],
          [-999.0, (0.0 / s, 255.0 / s, 0.0 / s)]]
    for j in range(len(bs)):
        if bs[j][0] < lag:
            break
    else:
        j = 0
    if j == 0 or j == len(bs) - 1:
        return bs[j][1]
    else:
        c = []
        dx = bs[j - 1][0] - bs[j][0]
        for i, y2 in enumerate(bs[j - 1][1]):
            y1 = bs[j][1][i]
            m = (y2 - y1) / dx
            c.append(m * (lag - bs[j][0]) + y1)
        return c

def color_bar():
    fff = plt.figure('ColorBar')
    ax = fff.add_subplot(111)
    ax.set_yticklabels([])
    plt.xlabel('Days')
    for j in range(180):
        i = j - 90.0
        c = complete2rgb(i)
        plt.plot([i], [1.0], 's', markersize=20, color=c, markeredgewidth=0.0, fillstyle='full')
    ar = plt.axis()
    boxx = [ar[0], ar[1], ar[1], ar[0], ar[0]]
    boxy = [-5.0, -5.0, 6.0, 6.0, -5.0]
    plt.plot(boxx, boxy, 'k')
    plt.axis('image')