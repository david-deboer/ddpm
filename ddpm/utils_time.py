from argparse import Namespace
import datetime
from numpy import floor
from dateutil.parser import parse
from copy import copy
from numpy import floor


def cadence_keys(cadence, date):
    if cadence == 'daily':
        cdate = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=23, minute=59).astimezone()
    elif cadence == 'monthly':
        ldom = last_day_of_month(date)
        cdate = datetime.datetime(year=date.year, month=date.month, day=ldom, hour=23, minute=59).astimezone()
    elif cadence == 'quarterly':
        qmon = 3 * int(floor((date.month-1)/3 + 1))
        ldom = last_day_of_month(datetime.datetime(year=date.year, month=qmon, day=28), False)
        cdate = datetime.datetime(year=date.year, month=qmon, day=ldom, hour=23, minute=59).astimezone()
    elif cadence == 'yearly':
        cdate = datetime.datetime(year=date.year, month=12, day=31, hour=23, minute=59).astimezone()
    return cdate


def last_day_of_month(t, return_datetime=False):
    next_mon = datetime.datetime(year=t.year, month=t.month, day=25).astimezone() + datetime.timedelta(days=10)
    ldom = datetime.datetime(year=next_mon.year, month=next_mon.month, day=1).astimezone() - datetime.timedelta(days=1)
    if return_datetime:
        return ldom
    return ldom.day


def datedeltastr(val, fmt='%Y-%m-%d %H:%M'):
    if isinstance(val, datetime.datetime):
        return val.strftime(fmt)
    elif isinstance(val, datetime.timedelta):
        return f"{val.days + val.seconds / 86400:.2f}"
    else:
        return None


def make_timezone(hours=None, name=None):
    if hours is None:
        return copy(datetime.datetime.now().astimezone().tzinfo)
    if name is None:
        sgn = '+' if float(hours) >= 0.0 else '-'
        name = f"UTC{sgn}{float(hours):.0f}"
    return datetime.timezone(datetime.timedelta(hours=float(hours)), name)


def datetimedelta(date, key=None, timezone=None):
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
        return make_timezone(hours=hr, name=name)

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

    if isinstance(date, str):
        date = parse(date).astimezone()

    if isinstance(date, datetime.date):
        date = datetime.datetime.combine(date, datetime.time())
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone)

    return date


def get_qtr_year_from_datetime(dt):
    for i, q in enumerate([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]):
        if dt.month in q:
            return {'qtr': i+1, 'yr':dt.year}


def get_fiscal_year(val, fy_month=7):
    fy = Namespace(year=None)
    if isinstance(val, str):
        if 'FY' in val.upper():
            ind = val.upper().index('FY')
            try:
                nval = int(val[ind+2:ind+6])
            except ValueError:
                try:
                    nval = int(val[ind+2:ind+4])
                except ValueError:
                    return fy
        else:
            try:
                nval = int(val)
            except ValueError:
                return fy
    elif isinstance(val, (int, float)):
        nval = int(val)
    elif isinstance(val, datetime.datetime):
        if val.mon < fy_month:
            nval = val.year
        else:
            nval = val.year + 1
    if nval < 1000:
        fy.year = nval + 2000
    else:
        fy.year = nval
    fy.start = datetime.datetime(year=fy.year-1, month=fy_month, day=1).astimezone()
    fy.stop = datetime.datetime(year=fy.year, month=fy_month, day=1).astimezone() - datetime.timedelta(days=1)
    return fy


def months_to_timedelta(starts, duration_mo):
    starts = parse(starts).astimezone()
    int_mo = int(floor(duration_mo))
    yr, mo = int_mo // 12, int_mo % 12
    dy = (duration_mo - int_mo) * 30.42
    new_month = starts.month + mo
    new_year = starts.year + yr
    if new_month > 12:
        new_month -= 12
        new_year += 1
    ends = datetime.datetime(year=new_year, month=new_month, day=1).astimezone() - datetime.timedelta(days=1) + datetime.timedelta(days=dy)
    duration = ends - starts
    return duration

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