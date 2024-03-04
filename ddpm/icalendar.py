import vobject
import datetime
from copy import copy
from . import project, components
from dateutil.parser import parse
import pytz


def to_dtz(val, time='00:00'):
    if isinstance(val, datetime.datetime):
        return val.astimezone()
    # From calev value
    try:
        hr, mn = [int(t) for t in time.split(':')]
        sc = 0
    except ValueError:
        hr, mn, sc = [int(t) for t in time.split(':')]
    return datetime.datetime(year=val.year, month=val.month, day=val.day, hour=hr, minute=mn, second=sc).astimezone()

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
        self.now = datetime.datetime.now().astimezone()

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
        iplot = project.Project(self.icsfn)
        entry_labels = []
        for era in eras:
            for event in sorted(self.events[era]):
                if not len(self.events[era][event]['summary']):
                    continue
                if self.events[era][event]['summary'][0] == '|':
                    clr = 'y'
                else:
                    clr = self.era_colors[era]
                if 'description' in self.events[era][event]['event'].contents:
                    if self.events[era][event]['event'].contents['description'][0].value == '?':
                        clr = 'c'
                this_entry = self.events[era][event]['summary']
                if this_entry in entry_labels:
                    entry_base = copy(this_entry)
                    ctr = 1
                    while this_entry in entry_labels:
                        ctr += 1
                        this_entry = f"{entry_base}-{ctr}"
                entry_labels.append(this_entry)
                iplot.add(components.Timeline(name=this_entry,
                                              begins=self.events[era][event]['dtstart'],
                                              ends=self.events[era][event]['dtend'],
                                              color=clr))
        iplot.chart(weekends=True, months=True)
    
    def ical_text(self, eras=['current', 'next', 'upcoming', 'future'], strfmt='%m/%d/%y'):
        strfmt += 'T%H:%M'
        for era in eras:
            for event in sorted(self.events[era]):
                print(f"{self.events[era][event]['dtstart'].strftime(strfmt)}  -  {self.events[era][event]['dtend'].strftime(strfmt)}   {self.events[era][event]['summary']}")

    def add(self, start, end, summary):
        dtstart = to_dtz(parse(start), '00:00')
        dtend = to_dtz(parse(end), '23:59')
        era = get_era(self.now, dtstart, dtend, upcoming=self.upcoming)
        key = copy(dtstart)
        while key in self.events:
            key += datetime.timedelta(seconds=1)
        self.events[era][key] = {'dtstart': dtstart,
                                 'dtend': dtend,
                                 'summary': '|' + summary}