import matplotlib.pyplot as plt
import datetime

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

def return_datetime(date, fmt='%Y-%m-%d'):
    if isinstance(date, datetime.datetime):
        return date
    elif isinstance(date, str):
        return datetime.datetime.strptime(date, fmt)
    else:
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