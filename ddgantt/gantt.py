from copy import copy
from . import plotting, gantt_util
import datetime
from argparse import Namespace
import hashlib
import csv


DATE_FIELDS = ['date', 'begins', 'ends', 'updated']
LIST_FIELDS = ['note', 'associated_with']
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


class _BaseEvent:
    base_attr_init = ['name', 'owner', 'status', 'note', 'updated', 'colinear']
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
                    self.status = 'none'
        if self.updated is not None:
            self.updated = gantt_util.return_datetime(self.updated)
        if self.note is None:
            self.note = []
        elif isinstance(self.note, str):
            self.note = [self.note]

    def add_note(self, note):
        self.note.append(note)


class Milestone(_BaseEvent):
    """
    """
    entry_names = ['name', 'date', 'owner', 'label', 'status', 'note', 'updated', 'lag', 'colinear', 'marker', 'color']
    def __init__(self, name, date, owner=None, label=None, status='other', note=None, updated='now', lag=None, colinear=None, marker='D', color=None):
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
        note : list
            General note to add
        updated : str, datetime
            Date of the current update
        lag : str, float, None
            how late(=) or early (-) as complete milestone was done
        colinear : str, None
            Key of other milestone to put on the same line
        marker : str
            Marker used for plotting
        color : str, None
            Color used for plotting, if None make based on statu/lag
        """
        super().__init__(name=name, owner=owner, status=status, note=note, updated=updated, colinear=colinear)
        self.date = gantt_util.return_datetime(date)
        self.label = label
        self.lag = lag
        self.marker = marker
        if self.status in ['other', 'moved'] and datetime.datetime.now() > self.date:
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
        self.key = hashlib.md5(hashstr).hexdigest()[:6]


class Task(_BaseEvent):
    entry_names = ['name', 'begins', 'ends', 'owner', 'label', 'status', 'note', 'updated', 'colinear', 'color']
    def __init__(self, name, begins, ends, owner=None, label=None, status=None, note=None, updated='now', colinear=None, color=None):
        super().__init__(name=name, owner=owner, status=status, note=note, updated=updated, colinear=colinear)
        self.begins = gantt_util.return_datetime(begins)
        self.ends = gantt_util.return_datetime(ends)
        self.label = label
        if color is None:
            self.color = gantt_util.color_palette[0]
        else:
            self.color = color
        hashstr = f"{name}-{self.begins.strftime('%Y%m%d')}-{self.ends.strftime('%Y%m%d')}".encode('ascii')
        self.key = hashlib.md5(hashstr).hexdigest()[:6]

    def __repr__(self):
        return f"{self.key}:  {self.name}  {self.begins} -  {self.ends}"


class Note:
    entry_names = ['note', 'date', 'associated_with']
    def __init__(self, note, date='now', associated_with=None):
        self.date = gantt_util.return_datetime(date)
        self.note = note
        if associated_with is None:
            self.associated_with = []
        elif isinstance(associated_with, str):
            self.associated_with = associated_with.split(',')
        elif isinstance(associated_with, list):
            self.associated_with = associated_with
        else:
            print(f"Invalid reference {associated_with}")
        hashstr = f"{note}-{self.date.strftime('%Y%m%d')}".encode('ascii')
        self.key = hashlib.md5(hashstr).hexdigest()[:6]

    def add_association(self, key):
        self.associated_with.append(key)


class Project:
    """
    Project
    """
    _SortInfo = {'milestone': {'begins': 'date', 'ends': 'date'},
                 'task': {}, 'note': {}}
    csv_header = ['name', 'date:begins', 'ends', 'owner', 'label', 'status', 'note', 'lag', 'color', 'marker', 'updated']
    event_types = ['task', 'milestone']
    other_types = ['note']
    def __init__(self, name, organization=None):
        self.entry_types = self.event_types + self.other_types
        self.name = name
        self.organization = organization
        self.milestones = {}
        self.tasks = {}
        self.notes = {}
        self.all_entry_keys = []
        self.colinear_map = {}
        self.earliest, self.latest = {}, {}
        self.updated = None
        for entry in self.entry_types:
            self.earliest[entry] = None
            self.latest[entry] = None

    def add_task(self, task):
        if task.key in self.all_entry_keys:
            print(f"Warning No-add: Key for {task.name} already added ({task.key}).")
            return
        self.all_entry_keys.append(task.key)
        self.tasks[task.key] = task
        if self.earliest['task'] is None:
            self.earliest['task'] = task.begins
        elif task.begins < self.earliest['task']:
            self.earliest['task'] = task.begins
        if self.latest['task'] is None:
            self.latest['task'] = task.ends
        elif task.ends > self.latest['task']:
            self.latest['task'] = task.ends
        if task.colinear is not None:
            self.colinear_map[task.key] = task.colinear

    def add_milestone(self, milestone):
        if milestone.key in self.all_entry_keys:
            print(f"Warning No-add: Key for {milestone.name} already added ({milestone.key}).")
            return
        self.all_entry_keys.append(milestone.key)
        self.milestones[milestone.key] = milestone
        if self.earliest['milestone'] is None:
            self.earliest['milestone'] = milestone.date
        elif milestone.date < self.earliest['milestone']:
            self.earliest['milestone'] = milestone.date
        if self.latest['milestone'] is None:
            self.latest['milestone'] = milestone.date
        elif milestone.date > self.latest['milestone']:
            self.latest['milestone'] = milestone.date
        if milestone.colinear is not None:
            self.colinear_map[milestone.key] = milestone.colinear

    def add_note(self, note):
        if note.key in self.all_entry_keys:
            print(f"Conflicting keys - not adding {note.note}")
            return
        self.all_entry_keys.append(note.key)
        self.notes[note.key] = note
        if self.earliest['note'] is None:
            self.earliest['note'] = note.date
        elif note.date < self.earliest['note']:
            self.earliest['note'] = note.date
        if self.latest['note'] is None:
            self.latest['note'] = note.date
        elif note.date > self.latest['note']:
            self.latest['note'] = note.date

    def _sort_(self, entry, sortby):
        dtype = f"sorted_{entry}s"
        setattr(self, dtype, {})
        SortInfo = self._SortInfo[entry]
        for this in getattr(self, f"{entry}s").values():
            sortkey = ''
            for par in sortby:
                if par in SortInfo:
                    upar = SortInfo[par]
                else:
                    upar = par
                uval = getattr(this, upar)
                if upar in DATE_FIELDS:
                    uval = uval.strftime('%Y%m%dT%H%M')
                sortkey += uval + '_'
            sortkey += f"_{entry[0]}"
            getattr(self, dtype)[sortkey] = this.key

    def _align_keys(self, ykeys):
        """
        Goes through colinear and puts them on the same line as first
        """
        mapkeys = []
        for ykey in ykeys:
            if ykey in self.colinear_map:
                mapkeys.append(self.colinear_map[ykey])
            else:
                mapkeys.append(ykey)
        return mapkeys

    def _get_event_extrema(self):
        chkmin, chkmax = [], []
        for event in self.event_types:
            if self.earliest[event] is not None:
                chkmin.append(self.earliest[event])
            if self.latest[event] is not None:
                chkmax.append(self.latest[event])
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
        allsortkeys = sorted(list(self.sorted_milestones.keys()) + list(self.sorted_tasks.keys()))
        dates = []
        labels = []
        plotpars = []
        ykeys = []  # keys lists the keys used, may be used to pu
        extrema = self._get_event_extrema()
        for sortkey in allsortkeys:
            if sortkey.endswith('__m'):
                this = self.milestones[self.sorted_milestones[sortkey]]
                dates.append([this.date, None])
                plotpars.append(Namespace(color=this.color, marker=this.marker, owner=this.owner))
            elif sortkey.endswith('__t'):
                this = self.tasks[self.sorted_tasks[sortkey]]
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
        allsortkeys = sorted(self.sorted_milestones.keys())
        dates = []
        status = []
        extrema = Namespace(min=self.earliest['milestone'], max=datetime.datetime.now())
        for sortkey in allsortkeys:
            this_milestone = self.milestones[self.sorted_milestones[sortkey]]
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

    def show_notes(self, sortby=['date', 'note']):
        self._sort_('note', sortby)
        for sortkey in self.sorted_notes:
            this = self.notes[self.sorted_notes[sortkey]]
            print(f"{this.note}  {this.date.strftime('%Y-%m-%d %H:%M')}  - ({', '.join(this.associated_with)})")

    def color_bar(self):
        gantt_util.color_bar()

    def csvread(self, loc, exportpy=False):
        fp = None
        print(f"Reading {loc}")
        if exportpy:
            fpexport = open(f"exportpy.py", 'w')
            print("Writing exportpy.py")
            print("from ddgantt import gantt\n", file=fpexport)
            print(f"project = gantt.Project('{self.name}', organization='{self.organization}')\n", file=fpexport)
        classes = {'Milestone': Milestone('x','now'), 'Task':  Task('x', 'now', 'now'), 'Note':  Note('x', 'now')}
        if loc.startswith('http'):
            data = gantt_util.load_sheet_from_url(loc)
            header = copy(data[0])
            reader = data[1:]
        else:
            fp = open(loc, 'r')
            reader = csv.reader(fp)
            header = next(reader)
        print(header)
        nind = header.index('name')
        eind = header.index('ends')
        ctr = 1
        for row in reader:
            dtype = 'Note'
            if len(row[eind].strip()):
                dtype = 'Task'
            elif len(row[nind].strip()):
                dtype = 'Milestone'
            kwargs = {}
            for hdrc, val in zip(header, row):
                for hdr in hdrc.split(':'):
                    if hdr in classes[dtype].entry_names:
                        if hdr in DATE_FIELDS:
                            kwargs[hdr] = gantt_util.return_datetime(val)
                        elif hdr in LIST_FIELDS and dtype != 'Note':
                            kwargs[hdr] = val.split('|')
                        elif hdr == 'color':
                            if val.startswith('('):
                                kwargs[hdr] = [float(_x) for _x in val.strip('()').split(',')]
                            else:
                                kwargs[hdr] = val
                        elif hdr == 'lag':
                            try:
                                kwargs[hdr] = float(val)
                            except ValueError:
                                kwargs[hdr] = 0.0
                        else:
                            kwargs[hdr] = val
                        break
            if exportpy:
                entryname = f"entry{ctr}"
                kwstr = []
                for kk, kv in kwargs.items():
                    if kk in DATE_FIELDS:
                        kv = f"'{kv.strftime('%Y-%m-%d %H:%M')}'"
                    elif isinstance(kv, str):
                        kv = f"'{kv}'"
                    kwstr.append(f"{kk}={kv}")
                kwstr = ', '.join(kwstr)
            if dtype == 'Note':
                if exportpy:
                    print(f"{entryname} = gantt.Note({kwstr})", file=fpexport)
                    print(f"project.add_note({entryname})", file=fpexport)
                self.add_note(Note(**kwargs))
            elif dtype == 'Milestone':
                if exportpy:
                    print(f"{entryname} = gantt.Milestone({kwstr})", file=fpexport)
                    print(f"project.add_milestone({entryname})", file=fpexport)
                self.add_milestone(Milestone(**kwargs))
            elif dtype == 'Task':
                if exportpy:
                    print(f"{entryname} = gantt.Task({kwstr})", file=fpexport)
                    print(f"project.add_task({entryname})", file=fpexport)
                self.add_task(Task(**kwargs))
            ctr += 1
        if fp is not None:
            fp.close()
        if exportpy:
            fpexport.close()

    def csvwrite(self, fn):
        print(f"Writing csv file {fn}")
        with open(fn, 'w') as fp:
            writer = csv.writer(fp)
            writer.writerow(self.csv_header)
            for entry in ['milestones', 'tasks', 'notes']:
                for this in getattr(self, entry).values():
                    row = []
                    for cols in self.csv_header:
                        found_value = False
                        for col in cols.split(':'):
                            try:
                                val = getattr(this, col)
                                found_value = True
                                if col in DATE_FIELDS:
                                    val = val.strftime('%Y-%m-%d %H:%M')
                                elif col in LIST_FIELDS and entry != 'notes':
                                    val = '|'.join([str(_x) for _x in val])
                                row.append(val)
                                break
                            except AttributeError:
                                continue
                        if not found_value:
                            row.append('')
                    writer.writerow(row)

