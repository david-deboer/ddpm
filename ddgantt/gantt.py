from copy import copy
from . import plotting, gantt_util
import datetime
from argparse import Namespace
import hashlib


DATE_FIELDS = ['date', 'begins', 'ends']
NOW = datetime.datetime.now()
PAST = datetime.datetime(year=2000, month=1, day=1)
FUTURE = datetime.datetime(year=2040, month=12, day=31)
STATUS_COLOR_B = {'complete': 'g', 'late': 'r', 'other': 'k', 'moved': 'y', 'removed': 'w', 'none': 'k'}
STATUS_COLOR = {
    'complete': gantt_util.color_palette[2],
    'late': 'r',
    'other': 'k',
    'none': 'k',
    'moved': gantt_util.color_palette[1],
    'removed': gantt_util.color_palette[4]
}


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
            try:
                self.status = float(self.status)
            except ValueError:
                if self.status not in STATUS_COLOR:
                    raise ValueError(f"Invalid status {self.status}")


class Milestone(_Base):
    def __init__(self, name, date, owner=None, label=None, status='other', lag=None, marker='D', color=None):
        super().__init__(name=name, owner=owner, status=status)
        self.date = gantt_util.return_datetime(date)
        self.label = label
        self.marker = marker
        if self.status in ['other', 'moved'] and NOW > self.date:
            self.status = 'late'
        if color is None:
            if status is None:
                self.color = 'k'
            elif status == 'complete' and lag is not None:
                self.color = gantt_util.lag2rgb(lag)
            else:
                self.color = STATUS_COLOR[self.status]
        else:
            self.color = color
        hashstr = f"{name}-{self.date.strftime('%Y%m%d')}".encode('ascii')
        self.key = hashlib.md5(hashstr).hexdigest()[:4]


class Task(_Base):
    def __init__(self, name, begins, ends, owner=None, label=None, status=None, color=None):
        super().__init__(name=name, owner=owner, status=status)
        self.begins = gantt_util.return_datetime(begins)
        self.ends = gantt_util.return_datetime(ends)
        self.label = label
        if color is None:
            self.color = gantt_util.color_palette[0]
        else:
            self.color = color
        hashstr = f"{name}-{self.begins.strftime('%Y%m%d')}-{self.ends.strftime('%Y%m%d')}".encode('ascii')
        self.key = hashlib.md5(hashstr).hexdigest()[:4]

class Project:
    _SortInfo = {'milestone': {'begins': 'date', 'ends': 'date'},
                 'task': {}}
    def __init__(self, name, organization=None):
        self.name = name
        self.organization = organization
        self.milestones = {}
        self.tasks = {}
        self.all_activity_keys = []

    def add_task(self, task):
        if task.key in self.all_activity_keys:
            raise ValueError(f"Key for {task.name} already added.")
        self.all_activity_keys.append(task.key)
        self.tasks[task.key] = task

    def add_milestone(self, milestone):
        if milestone.key in self.all_activity_keys:
            raise ValueError(f"Key for {milestone.name} already added.")
        self.all_activity_keys.append(milestone.key)
        self.milestones[milestone.key] = milestone

    def _sort_(self, entry, sortby):
        dtype = f"sorted_{entry}s"
        setattr(self, dtype, {})
        SortInfo = self._SortInfo[entry]
        for this in getattr(self, f"{entry}s").values():
            plotkey = ''
            for par in sortby:
                if par in SortInfo:
                    upar = SortInfo[par]
                else:
                    upar = par
                uval = getattr(this, upar)
                if upar in ['date', 'ends']:
                    if uval > self.latest[entry]:
                        self.latest[entry] = copy(uval)
                if upar in ['date', 'begins']:
                    if uval < self.earliest[entry]:
                        self.earliest[entry] = copy(uval)
                if upar in DATE_FIELDS:
                    uval = uval.strftime('%Y%m%dT%H%M')
                plotkey += uval + '_'
            plotkey += f"_{entry[0]}"
            getattr(self, dtype)[plotkey] = this.key

    def chart(self, sortby=['begins', 'name'], interval=None):
        """
        Make a gantt chart.

        Parameter
        ---------
        sortby : list
           fields to sort by, must be unique.  sort_info dicts map if needed
        """
        self.earliest = {'milestone': FUTURE, 'task': FUTURE}
        self.latest = {'milestone': PAST, 'task': PAST}
        self._sort_('task', sortby)
        self._sort_('milestone', sortby)
        allplotkeys = sorted(list(self.sorted_milestones.keys()) + list(self.sorted_tasks.keys()))
        dates = []
        labels = []
        plotpars = []
        extrema = Namespace(min=min(self.earliest['milestone'], self.earliest['task']),
                            max=max(self.latest['milestone'], self.latest['task']))
        for plotkey in allplotkeys:
            if plotkey.endswith('__m'):
                this_ms = self.milestones[self.sorted_milestones[plotkey]]
                dates.append([this_ms.date, None])
                labels.append(this_ms.name)
                plotpars.append(Namespace(color=this_ms.color, marker=this_ms.marker, owner=this_ms.owner))
            elif plotkey.endswith('__t'):
                this_task = self.tasks[self.sorted_tasks[plotkey]]
                dates.append([this_task.begins, this_task.ends])
                labels.append(this_task.name)
                plotpars.append(Namespace(color=this_task.color, status=this_task.status, owner=this_task.owner))
        plotting.gantt_chart(dates, labels, plotpars, extrema, interval=interval)

    def cumulative(self, sortby=['begins', 'name'], step=1.0, show=True):
        """
        Make a cumulative milestone chart.

        Parameter
        ---------
        sortby : list
           fields to sort by, must be unique.  sort_info dicts map if needed
        """
        self.earliest = {'milestone': FUTURE}
        self.latest = {'milestone': PAST}
        self._sort_('milestone', sortby)
        allplotkeys = sorted(self.sorted_milestones.keys())
        dates = []
        status = []
        extrema = Namespace(min=self.earliest['milestone'], max=NOW)
        for plotkey in allplotkeys:
            this_milestone = self.milestones[self.sorted_milestones[plotkey]]
            dates.append([this_milestone.date, None])
            status.append(Namespace(status=this_milestone.status))
        self.cdf = Namespace(num=len(dates), dates=[], values=[])
        this_date = copy(extrema.min)
        while this_date < extrema.max:
            self.cdf.dates.append(this_date)
            ctr = 0.0
            for i in range(len(status)):
                if this_date > dates[i][0] and status[i].status == 'complete':
                    ctr += 1.0
            self.cdf.values.append(ctr)
            this_date += datetime.timedelta(days=step)
        if show:
            plotting.cumulative_graph(self.cdf.dates, self.cdf.values, self.cdf.num)

    def color_bar(self):
        gantt_util.color_bar()