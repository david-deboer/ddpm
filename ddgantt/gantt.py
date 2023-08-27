import matplotlib.pyplot as plt
from copy import copy
from . import plot_gantt, gantt_util
import datetime
from argparse import Namespace


DATE_FIELDS = ['date', 'begins', 'ends']
NOW = datetime.datetime.now()
PAST = datetime.datetime(year=2000, month=1, day=1)
FUTURE = datetime.datetime(year=2040, month=12, day=31)
STATUS_COLOR = {'complete': 'g', 'late': 'r', 'other': 'k', 'moved': 'y', 'removed': 'w'}

class _Base:
    base_attr_init = ['name', 'owner', 'status']
    def __init__(self, **kwargs):
        for this_attr in self.base_attr_init:
            try:
                setattr(self, this_attr, kwargs[this_attr])
            except KeyError:
                print(f"Was expecting {this_attr} -- setting to None")
                setattr(self, this_attr, None)
        if isinstance(self.status, str):
            self.status = self.status.lower()
            if self.status not in STATUS_COLOR:
                raise ValueError(f"Invalid status {self.status}")


class Milestone(_Base):
    def __init__(self, name, date, owner=None, label=None, status='other', lag=None, marker='D', color=None):
        super().__init__(name=name, owner=owner, status=status)
        self.date = date
        self.label = label
        self.marker = marker
        if self.status in ['other', 'moved'] and NOW > self.date:
            self.status = 'late'
        if color is None:
            if status == 'complete' and lag is not None:
                self.color = gantt_util.lag2rgb(lag)
            else:
                self.color = STATUS_COLOR[self.status]
        else:
            self.color = color


class Task(_Base):
    def __init__(self, name, begins, ends, owner=None, label=None, status=None, color=None):
        super().__init__(name=name, owner=owner, status=status)
        self.begins = begins
        self.ends = ends
        self.label = label
        if color is None:
            self.color = 'b'
        else:
            self.color = color

class Project:
    _TaskSortInfo = {}
    _MilestoneSortInfo = {'begins': 'date', 'ends': 'date'}
    def __init__(self, name, organization=None):
        self.name = name
        self.organization = organization
        self.milestones = []
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def add_milestone(self, milestone):
        self.milestones.append(milestone)

    def _sort_(self, entry, sortby):
        entries = f"{entry}s"
        dtype = f"sorted_{entries}"
        setattr(self, f"earliest_{entry.lower()}", FUTURE)
        setattr(self, f"latest_{entry.lower()}", PAST)
        setattr(self, dtype, {})
        SortInfo = getattr(self, f"_{entry.capitalize()}SortInfo")
        for this in getattr(self, entries):
            key = ''
            for par in sortby:
                if par in SortInfo:
                    upar = SortInfo[par]
                else:
                    upar = par
                uval = getattr(this, upar)
                if upar in ['date', 'ends']:
                    if uval > self.latest_task:
                        self.latest_task = copy(uval)
                if upar in ['date', 'begins']:
                    if uval < self.earliest_task:
                        self.earliest_task = copy(uval)
                if upar in DATE_FIELDS:
                    uval = uval.strftime('%Y%m%dT%H%M')
                key += uval + '_'
            key += f"_{entry[0]}"
            getattr(self, dtype)[key] = this

    def plot(self, sortby=['begins', 'name']):
        """
        Make a gantt chart.

        Parameter
        ---------
        sortby : list
           fields to sort by, must be unique.  sort_info dicts map if needed
        """
        self._sort_('task', sortby)
        self._sort_('milestone', sortby)
        allkeys = sorted(list(self.sorted_milestones.keys()) + list(self.sorted_tasks.keys()))
        dates = []
        labels = []
        plotpars = []
        extrema = Namespace(min=min(self.earliest_milestone, self.earliest_task), max=max(self.latest_milestone, self.latest_task))
        for key in allkeys:
            if key.endswith('__m'):
                this_milestone = self.sorted_milestones[key]
                dates.append([this_milestone.date, None])
                labels.append(this_milestone.name)
                plotpars.append(Namespace(color=this_milestone.color, marker=this_milestone.marker))
            elif key.endswith('__t'):
                this_task = self.sorted_tasks[key]
                dates.append([this_task.begins, this_task.ends])
                labels.append(this_task.name)
                plotpars.append(Namespace(color=this_task.color))
        plot_gantt.plotGantt(dates, labels, plotpars, extrema)