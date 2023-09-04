import matplotlib.pyplot as plt
import datetime
import requests
import csv

color_palette = [
    (0.12156862745098039, 0.4666666666666667, 0.7058823529411765, 1.0),
    (1.0, 0.4980392156862745, 0.054901960784313725, 1.0),
    (0.17254901960784313, 0.6274509803921569, 0.17254901960784313, 1.0),
    (0.8392156862745098, 0.15294117647058825, 0.1568627450980392, 1.0),
    (0.5803921568627451, 0.403921568627451, 0.7411764705882353, 1.0),
    (0.5490196078431373, 0.33725490196078434, 0.29411764705882354, 1.0)
        ]

def load_sheet_from_url(url):
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

def datetimedelta(date, key=None, fmt=['%Y-%m-%d', '%y/%m/%d', '%Y-%m-%d %H:%M']):
    if key == 'duration':
        if isinstance(date, datetime.timedelta):
            return date
        try:
            return datetime.timedelta(days = float(date))
        except (TypeError, ValueError):
            return None
    if date == 'now':
        return datetime.datetime.now()
    if isinstance(date, datetime.datetime):
        return date
    if isinstance(date, str):
        for this_fmt in fmt:
            try:
                dt = datetime.datetime.strptime(date, this_fmt)
                return dt
            except ValueError:
                pass
    raise ValueError(f"Invalid date format {type(date)} - {date}")

def lag2rgb(lag):
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
        c = lag2rgb(i)
        plt.plot([i], [1.0], 's', markersize=20, color=c, markeredgewidth=0.0, fillstyle='full')
    ar = plt.axis()
    boxx = [ar[0], ar[1], ar[1], ar[0], ar[0]]
    boxy = [-5.0, -5.0, 6.0, 6.0, -5.0]
    plt.plot(boxx, boxy, 'k')
    plt.axis('image')