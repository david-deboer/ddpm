import matplotlib.pyplot as plt
import requests
import csv


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