from copy import copy
from . import plotting, gantt_util
import datetime
from argparse import Namespace
import hashlib
import csv


DATE_FIELDS = ['date', 'begins', 'ends']
NOW = datetime.datetime.now()
PAST = datetime.datetime(year=2000, month=1, day=1)
FUTURE = datetime.datetime(year=2040, month=12, day=31)
# STATUS_COLOR = {'complete': 'g', 'late': 'r', 'other': 'k', 'moved': 'y', 'removed': 'w', 'none': 'k'}
STATUS_COLOR = {
    'complete': gantt_util.color_palette[2],
    'late': 'r',
    'other': 'k',
    'none': 'k',
    'moved': gantt_util.color_palette[1],
    'removed': gantt_util.color_palette[4]
}


class _Base:
    base_attr_init = ['name', 'owner', 'status', 'colinear']
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
    """
    """
    ms_columns = ['name', 'date', 'owner', 'label', 'status', 'lag', 'colinear', 'marker', 'color']
    def __init__(self, name, date, owner=None, label=None, status='other', lag=None, colinear=None, marker='D', color=None):
        """
        Parameters
        ----------
        name : str
            Name of milestone
        date : str, datetime
            Date of milestone
        owner : str, None
            Owner of the milestone
        label : str, None
            Additional label associated 
        status : str, None
            Status of milestone (see above list in STATUS_COLOR)
        lag : str, float, None
            how late(=) or early (-) as complete milestone was done
        colinear : str, None
            Key of other milestone to put on the same line
        marker : str
            Marker used for plotting
        color : str, None
            Color used for plotting, if None make based on statu/lag
        """
        super().__init__(name=name, owner=owner, status=status, colinear=colinear)
        self.date = gantt_util.return_datetime(date)
        self.label = label
        self.lag = lag
        self.marker = marker
        if self.status in ['other', 'moved'] and NOW > self.date:
            self.status = 'late'
        if color is None:
            if status is None:
                self.color = 'k'
            elif status == 'complete' and lag is not None:
                if abs(lag) > 1.0:
                    self.color = gantt_util.lag2rgb(lag)
                else:
                    self.color = STATUS_COLOR['complete']
            else:
                self.color = STATUS_COLOR[self.status]
        else:
            self.color = color
        hashstr = f"{name}-{self.date.strftime('%Y%m%d')}".encode('ascii')
        self.key = hashlib.md5(hashstr).hexdigest()[:4]


class Task(_Base):
    task_columns = ['name', 'begins', 'ends', 'owner', 'label', 'status', 'colinear', 'color']
    def __init__(self, name, begins, ends, owner=None, label=None, status=None, colinear=None, color=None):
        super().__init__(name=name, owner=owner, status=status, colinear=colinear)
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
    csv_header = ['name', 'date:begins', 'ends', 'owner', 'label', 'status', 'lag', 'color', 'marker']
    entry_types = ['task', 'milestone']
    def __init__(self, name, organization=None):
        self.name = name
        self.organization = organization
        self.milestones = {}
        self.tasks = {}
        self.all_activity_keys = []
        self.earliest, self.latest = {}, {}
        for entry in self.entry_types:
            self.earliest[entry] = None
            self.latest[entry] = None

    def add_task(self, task):
        if task.key in self.all_activity_keys:
            raise ValueError(f"Key for {task.name} already added.")
        self.all_activity_keys.append(task.key)
        self.tasks[task.key] = task
        if self.earliest['task'] is None:
            self.earliest['task'] = task.begins
        elif task.begins < self.earliest['task']:
            self.earliest['task'] = task.begins
        if self.latest['task'] is None:
            self.latest['task'] = task.ends
        elif task.ends > self.latest['task']:
            self.latest['task'] = task.ends

    def add_milestone(self, milestone):
        if milestone.key in self.all_activity_keys:
            raise ValueError(f"Key for {milestone.name} already added.")
        self.all_activity_keys.append(milestone.key)
        self.milestones[milestone.key] = milestone
        if self.earliest['milestone'] is None:
            self.earliest['milestone'] = milestone.date
        elif milestone.date < self.earliest['milestone']:
            self.earliest['milestone'] = milestone.date
        if self.latest['milestone'] is None:
            self.latest['milestone'] = milestone.date
        elif milestone.date > self.latest['milestone']:
            self.latest['milestone'] = milestone.date


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
                if upar in DATE_FIELDS:
                    uval = uval.strftime('%Y%m%dT%H%M')
                plotkey += uval + '_'
            plotkey += f"_{entry[0]}"
            getattr(self, dtype)[plotkey] = this.key

    def _align_keys(self, ykeys):
        """
        Goes through colinear and puts them on the same line as first
        """
        print("G157:  CURENTLY ALIGN DOES NOTHING")
        return ykeys

    def _get_extrema(self):
        chkmin, chkmax = [], []
        for entry in self.entry_types:
            if self.earliest[entry] is not None:
                chkmin.append(self.earliest[entry])
            if self.latest[entry] is not None:
                chkmax.append(self.latest[entry])
        return Namespace(min=min(chkmin), max=max(chkmax))

    def chart(self, sortby=['begins', 'name', 'ends'], interval=None):
        """
        Make a gantt chart.

        Parameter
        ---------
        sortby : list
           fields to sort by, must be unique.  sort_info dicts map if needed
        """
        self._sort_('task', sortby)
        self._sort_('milestone', sortby)
        allplotkeys = sorted(list(self.sorted_milestones.keys()) + list(self.sorted_tasks.keys()))
        dates = []
        labels = []
        plotpars = []
        ykeys = []  # keys lists the keys used, may be used to pu
        extrema = self._get_extrema()
        for plotkey in allplotkeys:
            if plotkey.endswith('__m'):
                this = self.milestones[self.sorted_milestones[plotkey]]
                dates.append([this.date, None])
                plotpars.append(Namespace(color=this.color, marker=this.marker, owner=this.owner))
            elif plotkey.endswith('__t'):
                this = self.tasks[self.sorted_tasks[plotkey]]
                dates.append([this.begins, this.ends])
                plotpars.append(Namespace(color=this.color, status=this.status, owner=this.owner))
            labels.append(this.name)
            ykeys.append(this.key)
        ykeys = self._align_keys(ykeys)
        plotting.gantt_chart(dates, labels, plotpars, ykeys, extrema, interval=interval)

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

    def csvread(self, fn):
        print("DOESN'T DO ANYTHING YET.")
        print(f"Reading csv file {fn}")
        with open(fn, 'r') as fp:
            reader = csv.reader(fp)
            header = next(reader)
            for row in reader:
                print(row)

    def csvwrite(self, fn):
        print(f"Writing csv file {fn}")
        with open(fn, 'w') as fp:
            writer = csv.writer(fp)
            writer.writerow(self.csv_header)
            for entry in ['milestones', 'tasks']:
                for this in getattr(self, entry).values():
                    row = []
                    for cols in self.csv_header:
                        for col in cols.split(':'):
                            try:
                                val = getattr(this, col)
                                row.append(val)
                            except AttributeError:
                                continue
                    writer.writerow(row)