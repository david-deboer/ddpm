import vobject
import datetime
from copy import copy
import matplotlib.pyplot as plt
from my_utils import time_data_tools as tdt
import pytz


def to_dtz(val, time='00:00'):
    if isinstance(val, datetime.datetime):
        return val.astimezone()
    hr = int(time.split(':')[0])
    mn = int(time.split(':')[1])
    dt = datetime.datetime(year=val.year, month=val.month, day=val.day, hour=hr, minute=mn)
    return dt.astimezone()

def get_era(now, dtstart, dtend, upcoming):
    if dtend < now:
        return 'past'
    if dtstart <= now:
        return 'current'
    if (dtstart - now).days < upcoming:
        return 'upcoming'
    return 'future'


class iCal:
    def __init__(self, icsfn='Hard Constraints.ics'):
        self.icsfn = icsfn
        self._make_tzid_convert()
        self.events = {'past': {}, 'current': {}, 'next': {}, 'upcoming': {}, 'future': {}}
        self.era_colors = {'past': '.7', 'current': 'g', 'next': 'r', 'upcoming': 'b', 'future': 'k'}
        self.now = to_dtz(datetime.datetime.now())

    def _make_tzid_convert(self):
        self.TZID = {}
        for ctz in pytz.common_timezones:
            offset = f"GMT{datetime.datetime.now(pytz.timezone(ctz)).strftime('%z')}"
            self.TZID[offset] = ctz  # ok to just keep the last

    def read_ics(self, upcoming=30):
        print(f"Reading {self.icsfn}")
        self.upcoming = upcoming
        in_event = False
        next_event = None
        with open(self.icsfn, 'r') as fp:
            for line in fp:
                if line.startswith('END:VCALENDAR'):
                    break
                elif line.startswith('BEGIN:VEVENT'):
                    in_event = True
                    this_entry = line
                elif in_event and line.startswith('END:VEVENT'):
                    this_entry += line
                    calev = vobject.readOne(this_entry)
                    dtstart = to_dtz(calev.contents['dtstart'][0].value, '00:00')
                    dtend = to_dtz(calev.contents['dtend'][0].value, '23:59')
                    era = get_era(self.now, dtstart, dtend, upcoming=self.upcoming)
                    key = to_dtz(calev.contents['dtstart'][0].value)
                    while key in self.events:
                        key += datetime.timedelta(seconds=1)
                    self.events[era][key] = {'dtstart': dtstart,
                                        'dtend': dtend,
                                        'summary': copy(calev.contents['summary'][0].value),
                                        'event': copy(calev)}
                    if era == 'upcoming':
                        if next_event is None or (key - self.now) < (next_event - self.now):
                            next_event = copy(key)
                    in_event = False
                elif in_event:
                    if 'TZID=GMT' in line:
                        for tz, id in self.TZID.items():
                            if tz in line:
                                this_entry += line.replace(tz, id)
                    else:
                        this_entry += line
        if next_event is not None:
            self.events['next'][next_event] = copy(self.events['upcoming'][next_event])
            del self.events['upcoming'][next_event]

    def ical_plot(self, eras = ['future', 'upcoming', 'next', 'current'], no_text=False):
        # Get limits
        early = to_dtz(datetime.datetime(year=2030, month=12, day=31))
        late = to_dtz(datetime.datetime(year=2010, month=1, day=1))
        ctr = 0
        for era in eras:
            for i, event in enumerate(sorted(self.events[era], reverse=True)):
                if self.events[era][event]['dtstart'] < early:
                    early = copy(self.events[era][event]['dtstart'])
                if self.events[era][event]['dtend'] > late:
                    late = copy(self.events[era][event]['dtend'])
                ctr += 1

        # Paint calendar
        plt.figure(self.icsfn)
        # ... show weekends
        first_sat = copy(early)
        while first_sat.weekday() != 5:
            first_sat += datetime.timedelta(days=1)
        this_date = copy(first_sat)
        while this_date < late:
            plt.fill_between([this_date, this_date + datetime.timedelta(days=2)], [ctr+10, ctr+10], -10, color='lightcyan')
            this_date += datetime.timedelta(days=7)
        # ... months
        plt.plot([self.now, self.now], [-10, ctr+10], 'c--', lw=3)
        if early.day < 10:
            first_day = datetime.datetime(year=early.year, month=early.month, day=1)
            plt.plot([first_day, first_day], [-10, ctr+10], '--', color='0.7')
        this_day = to_dtz(tdt.last_day_of_month(early, return_datetime=True)) + datetime.timedelta(days=1)
        while this_day < late:
            plt.plot([this_day, this_day], [-10, ctr+10], '--', color='0.7')
            this_day = to_dtz(tdt.last_day_of_month(this_day, return_datetime=True)) + datetime.timedelta(days=1)
        if late.day > 20:
            this_day = to_dtz(tdt.last_day_of_month(late, return_datetime=True)) + datetime.timedelta(days=1)
            plt.plot([this_day, this_day], [-10, ctr+10], '--', color='0.7')

        # Include events
        ctr = 0
        for era in eras:
            for i, event in enumerate(sorted(self.events[era], reverse=True)):
                if not len(self.events[era][event]['summary']):
                    continue
                if self.events[era][event]['summary'][0] == '|':
                    clr = 'y'
                else:
                    clr = self.era_colors[era]
                if 'description' in self.events[era][event]['event'].contents:
                    if self.events[era][event]['event'].contents['description'][0].value == '?':
                        clr = 'c'
                mdpt = self.events[era][event]['dtstart'] + (self.events[era][event]['dtend'] - self.events[era][event]['dtstart'])/2.0
                plt.plot(mdpt, ctr, 's', color=clr)
                plt.plot([self.events[era][event]['dtstart'], self.events[era][event]['dtend']], [ctr, ctr], clr, lw=8)
                if self.events[era][event]['summary'][0] == '|':
                    txt = self.events[era][event]['summary'][1:]
                else:
                    txt = self.events[era][event]['summary']
                if not no_text:
                    plt.text(self.events[era][event]['dtend'], ctr, txt[:80])
                ctr += 1
        plt.axis(ymin=-ctr/20, ymax=(ctr-1+ctr/20))
    
    def ical_text(self, eras=['current', 'next', 'upcoming', 'future'], strfmt='%m/%d/%y'):
        strfmt += 'T%H:%M'
        for era in eras:
            for event in sorted(self.events[era]):
                print(f"{self.events[era][event]['dtstart'].strftime(strfmt)}  -  {self.events[era][event]['dtend'].strftime(strfmt)}   {self.events[era][event]['summary']}")

    def add(self, start, end, summary):
        dtstart = to_dtz(tdt.get_datetime(start), '00:00')
        dtend = to_dtz(tdt.get_datetime(end), '23:59')
        era = get_era(self.now, dtstart, dtend, upcoming=self.upcoming)
        key = copy(dtstart)
        while key in self.events:
            key += datetime.timedelta(seconds=1)
        self.events[era][key] = {'dtstart': dtstart,
                                 'dtend': dtend,
                                 'summary': '|' + summary}