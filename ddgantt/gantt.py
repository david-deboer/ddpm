from copy import copy
from . import plotting, gantt_util
import datetime
from argparse import Namespace
import hashlib
import csv


DATE_FIELDS = ['date', 'begins', 'ends', 'updated', 'duration']
LIST_FIELDS = ['note', 'predecessors', 'groups', 'reference']
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


class Entry:
    def __init__(self, name, **kwargs):
        # Set parameter defaults to None
        for par in self.parameters:
            setattr(self, par, None)
        self.updated = gantt_util.datetimedelta('now')

        # Update parameters
        self.name = name
        for key, val in kwargs.items():
            if key not in self.parameters:
                print(f"Invalid key {key} in {self.name}")
                continue
            if key in DATE_FIELDS:
                setattr(self, key, gantt_util.datetimedelta(val, key))
            elif key in LIST_FIELDS and isinstance(val, str):
                setattr(self, key, val.split(','))
            else:
                setattr(self, key, val)

        if self.note is None:
            self.note = []
        elif isinstance(self.note, str):
            self.note = [self.note]

        if isinstance(self.color, str) and self.color.startswith('('):
            self.color = [float(_x) for _x in self.color.strip('()').split(',')]

        try:
            self.status = float(self.status)
        except (ValueError, TypeError, AttributeError):
            pass
        try:
            self.lag = float(self.lag)
        except (ValueError, TypeError, AttributeError):
            pass

    def add_note(self, note):
        self.note.append(note)


class Milestone(Entry):
    """
    """
    def __init__(self, name, date, **kwargs):
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
            Additional label associated - if not None, this will be used in the chart
        status : str, None
            Status of milestone (see above list in STATUS_COLOR) for milestones, use
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
            Color used for plotting, if None or 'auto' make based on status/lag
        """
        self.parameters = ['name', 'date', 'owner', 'label', 'status', 'note', 'updated',
                           'lag', 'predecessors', 'groups', 'colinear', 'marker', 'color']
        if name is None:
            return
        super().__init__(name=name, **kwargs)
        self.date = gantt_util.datetimedelta(date)
        if self.marker is None:
            self.marker = 'D'

        # Make key
        hashstr = f"{self.name}-{self.date.strftime('%Y%m%d')}".encode('ascii')
        self.key = hashlib.md5(hashstr).hexdigest()[:6]

    def __repr__(self):
        return f"{self.key}:  {self.name}  {self.date} "

    def get_color(self):
        if self.color is None or self.color == 'auto':
            pass
        else:
            return self.color
        if self.status != 'complete' and datetime.datetime.now() > self.date:
            return STATUS_COLOR['late']
        if self.status == 'complete' and self.lag is not None:
            if abs(self.lag) > 1.0:
                return gantt_util.lag2rgb(self.lag)
            return STATUS_COLOR['complete']
        if self.status in STATUS_COLOR:
            return STATUS_COLOR[self.status]
        return STATUS_COLOR['other']


class Timeline(Entry):
    tl_parameters = ['name', 'begins', 'ends', 'duration', 'note', 'updated', 'colinear',
                     'predecessors', 'groups', 'label', 'color']
    def __init__(self, name, **kwargs):
        try:
            self.parameters += self.tl_parameters
        except AttributeError:
            self.parameters = self.tl_parameters
        if name is None:
            return
        super().__init__(name=name, **kwargs)

        # Check/get timing
        provided_timing = []
        for key in ['begins', 'ends', 'duration']:
            if key in kwargs and isinstance(getattr(self, key), (datetime.datetime, datetime.timedelta)):
                provided_timing.append(key)
        if len(provided_timing) == 3:
            if gantt_util.datedeltastr(self.ends-self.begins) != gantt_util.datedeltastr(self.duration):
                raise ValueError(f"{self.name}:  can't specify time endpoints and duration incorrectly")
            self.duration = self.ends - self.begins  # Make match exactly.
        else:
            if len(provided_timing) != 2:
                raise ValueError(f"{self.name}:  not enough timing parameters provided")
            if 'duration' not in provided_timing:
                self.duration = self.ends - self.begins
            elif 'ends' not in provided_timing:
                self.ends = self.begins + self.duration
            elif 'begins' not in provided_timing:
                self.begins = self.ends - self.duration

        hashstr = f"{name}-{self.begins.strftime('%Y%m%d')}-{self.ends.strftime('%Y%m%d')}".encode('ascii')
        self.key = hashlib.md5(hashstr).hexdigest()[:6]

    def __repr__(self):
        return f"{self.key}:  {self.name}  {self.begins} -  {self.ends}"

    def get_color(self):
        if self.color is None or self.color == 'auto':
            return gantt_util.color_palette[0]
        return self.color

    def add_note(self, note):
        self.note.append(note)


class Task(Timeline):
    def __init__(self, name, **kwargs):
        self.parameters = ['owner', 'status', 'lag']
        super().__init__(name=name, **kwargs)

    def get_color(self):
        if self.color is None or self.color == 'auto':
            if isinstance(self.status, float):
                now = datetime.datetime.now()
                if int(self.status) != 100 and now > self.ends:
                    return STATUS_COLOR['late']
                if self.begins > now:
                    return gantt_util.color_palette[0]
                if self.lag is not None:
                    return gantt_util.lag2rgb(self.lag)
                print("GU165: will need to finish the taskbar color logic")
                pc_elapsed = 100.0 * (now - self.begins) / self.duration
                lag = 2.0 * (pc_elapsed - self.status)
                return gantt_util.lag2rgb(lag)
            return gantt_util.color_palette[0]
        return self.color

class Note:
    parameters = ['jot', 'date', 'reference']
    def __init__(self, jot, date='now', reference=None):
        if jot is None:
            return
        self.date = gantt_util.datetimedelta(date)
        self.jot = jot
        if reference is None:
            self.reference = []
        elif isinstance(reference, str):
            self.reference = reference.split(',')
        elif isinstance(reference, list):
            self.reference = reference
        else:
            print(f"Invalid reference {reference}")
        hashstr = f"{jot}-{self.date.strftime('%Y%m%d')}".encode('ascii')
        self.key = hashlib.md5(hashstr).hexdigest()[:6]

    def add_reference(self, key):
        self.reference.append(key)


class Project:
    """
    Project
    """
    columns = ['name', 'begins:date', 'ends', 'duration', 'colinear', 'color', 'status', 'groups', 'label',
               'lag', 'marker', 'note:jot', 'owner', 'predecessors:reference', 'updated', 'type', 'key']
    chart_types = ['milestone', 'timeline', 'task']
    event_types = ['milestone', 'task']
    other_types = ['note', 'timeline']
    def __init__(self, name, organization=None):
        self.entry_types = self.event_types + self.other_types
        self.name = name
        self.organization = organization
        for entry_type in self.entry_types:
            setattr(self, f"{entry_type}s", {})
        self.all_entry_keys = []
        self.colinear_map = {}
        self.earliest, self.latest = {}, {}
        self.updated = None
        for entry in self.entry_types:
            self.earliest[entry] = None
            self.latest[entry] = None

    def _add_entry(self, entry_type, entry):
        if entry.key in self.all_entry_keys:
            print(f"Warning '{entry_type}': Key for {entry.name} already added ({entry.key}).")
            return
        self.all_entry_keys.append(entry.key)
        if entry_type in ['milestone', 'note']:
            early_date = copy(entry.date)
            late_date = copy(entry.date)
        else:
            early_date = copy(entry.begins)
            late_date = copy(entry.ends)
        if self.earliest[entry_type] is None:
            self.earliest[entry_type] = early_date
        elif early_date < self.earliest[entry_type]:
            self.earliest[entry_type] = early_date
        if self.latest[entry_type] is None:
            self.latest[entry_type] = late_date
        elif late_date > self.latest[entry_type]:
            self.latest[entry_type] = late_date
        try:
            if entry.colinear is not None:
                self.colinear_map[entry.key] = entry.colinear
        except AttributeError:
            return

    def add_timeline(self, timeline):
        self._add_entry('timeline', timeline)
        self.timelines[timeline.key] = timeline

    def add_task(self, task):
        self._add_entry('task', task)
        self.tasks[task.key] = task

    def add_milestone(self, milestone):
        self._add_entry('milestone', milestone)
        self.milestones[milestone.key] = milestone

    def add_note(self, note):
        self._add_entry('note', note)
        self.notes[note.key] = note

    def _sort_(self, entry, sortby):
        entry_type = f"sorted_{entry}s"
        setattr(self, entry_type, {})
        for this in getattr(self, f"{entry}s").values():
            sortkey = ''
            for upar in sortby:
                try:
                    sortkey += str(getattr(this, upar)) + '_'
                except AttributeError:
                    continue
            sortkey += f"_{entry}"
            getattr(self, entry_type)[sortkey] = this.key

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
        for event in self.chart_types:
            if self.earliest[event] is not None:
                chkmin.append(self.earliest[event])
            if self.latest[event] is not None:
                chkmax.append(self.latest[event])
        chkmin = None if not len(chkmin) else min(chkmin)
        chkmax = None if not len(chkmax) else max(chkmax)
        return Namespace(min=chkmin, max=chkmax)

    def _get_sorted_chart_keys(self, to_chart):
        elist = []
        for etype in to_chart:
            elist += list(getattr(self, f"sorted_{etype}s").keys())
        return sorted(elist)

    def chart(self, chart='all', sortby=['begins', 'date', 'name', 'ends'], interval=None):
        """
        Make a gantt chart.

        Parameter
        ---------
        sortby : list
           fields to sort by
        """
        if chart == 'all':
            chart = self.chart_types
        for sort_this in chart:
            self._sort_(sort_this, sortby)
        allsortkeys = self._get_sorted_chart_keys(chart)
        dates = []
        labels = []
        plotpars = []
        ykeys = []  # keys lists the keys used, used to make the vertical axis including colinear
        extrema = self._get_event_extrema()
        for sortkey in allsortkeys:
            if sortkey.endswith('__milestone'):
                this = self.milestones[self.sorted_milestones[sortkey]]
                dates.append([this.date, None])
                plotpars.append(Namespace(color=this.get_color(), marker=this.marker, owner=this.owner))
            elif sortkey.endswith('__timeline'):
                this = self.timelines[self.sorted_timelines[sortkey]]
                dates.append([this.begins, this.ends])
                plotpars.append(Namespace(color=this.get_color(), status=None, owner=None))
            elif sortkey.endswith('__task'):
                this = self.tasks[self.sorted_tasks[sortkey]]
                dates.append([this.begins, this.ends])
                plotpars.append(Namespace(color=this.get_color(), status=this.status, owner=this.owner))
            if this.label is not None:
                labels.append(this.label)
            else:
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

    def show_notes(self, sortby=['date', 'jot']):
        self._sort_('note', sortby)
        for sortkey in self.sorted_notes:
            this = self.notes[self.sorted_notes[sortkey]]
            print(f"{this.jot}  {this.date.strftime('%Y-%m-%d %H:%M')}  - ({', '.join(this.reference)})")

    def color_bar(self):
        gantt_util.color_bar()

    def csvread(self, loc, export_gen_script=False):
        fp = None
        print(f"Reading {loc}")
        if export_gen_script:
            fpexport = open(f"export_gen_script.py", 'w')
            print("Writing export_gen_script.py")
            print("from ddgantt import gantt\n", file=fpexport)
            print(f"project = gantt.Project('{self.name}', organization='{self.organization}')\n", file=fpexport)
        classes = {'milestone': Milestone(None, 'now'), 'timeline': Timeline(None), 'task':  Task(None), 'note':  Note(None)}
        if loc.startswith('http'):
            data = gantt_util.load_sheet_from_url(loc)
            header = copy(data[0])
            reader = data[1:]
        else:
            fp = open(loc, 'r')
            reader = csv.reader(fp)
            header = next(reader)
        ctr = 1
        for row in reader:
            entry_type = row[header.index('type')]
            kwargs = {}
            for hdrc, val in zip(header, row):
                for hdr in hdrc.split(':'):
                    if hdr in classes[entry_type].parameters:
                        if val is None or not len(val):
                            kwargs[hdr] = None
                        elif hdr in DATE_FIELDS:
                            kwargs[hdr] = gantt_util.datetimedelta(val, hdr)
                        elif hdr in LIST_FIELDS:
                            kwargs[hdr] = val.split('|')
                        else:
                            kwargs[hdr] = val
                        break
            if export_gen_script:
                entryname = f"entry{ctr}"
                kwstr = []
                for kk, kv in kwargs.items():
                    if kv is None:
                        kv = 'None'
                    elif kk in DATE_FIELDS:
                        kv = gantt_util.datedeltastr(kv)
                    elif kk in LIST_FIELDS:
                        kv = '|'.join(kv)
                    elif isinstance(kv, str):
                        kv = f"'{kv}'"
                    kwstr.append(f"{kk}={kv}")
                kwstr = ', '.join(kwstr)
            if entry_type == 'note':
                if export_gen_script:
                    print(f"{entryname} = gantt.Note(jot='{jot}', date='{date.strftime('%Y-%m-%d %H:%M')}', {kwstr})", file=fpexport)
                    print(f"project.add_note({entryname})", file=fpexport)
                self.add_note(Note(jot=jot, date=date, **kwargs))
            elif entry_type == 'milestone':
                if export_gen_script:
                    print(f"{entryname} = gantt.Milestone(name='{name}', date='{date.strftime('%Y-%m-%d %H:%M')}', {kwstr})", file=fpexport)
                    print(f"project.add_milestone({entryname})", file=fpexport)
                self.add_milestone(Milestone(name=name, date=date, **kwargs))
            elif entry_type == 'timeline':
                if export_gen_script:
                    print(f"{entryname} = gantt.Timeline(name='{name}', {kwstr})", file=fpexport)
                    print(f"project.add_timeline({entryname})", file=fpexport)
                self.add_timeline(Timeline(name=name, **kwargs))
            elif entry_type == 'task':
                if export_gen_script:
                    print(f"{entryname} = gantt.Task(name='{name}', {kwstr})", file=fpexport)
                    print(f"project.add_task({entryname})", file=fpexport)
                self.add_task(Task(name=name, **kwargs))
            ctr += 1
        if fp is not None:
            fp.close()
        if export_gen_script:
            fpexport.close()

    def csvwrite(self, fn):
        print(f"Writing csv file {fn}")
        with open(fn, 'w') as fp:
            writer = csv.writer(fp)
            writer.writerow(self.columns)
            for entry in ['milestones', 'timelines', 'tasks', 'notes']:
                for this in getattr(self, entry).values():
                    row = []
                    for cols in self.columns:
                        added = False
                        for col in cols.split(':'):
                            try:
                                val = getattr(this, col)
                                if val is None:
                                    val = ''
                                elif col in DATE_FIELDS:
                                    val = gantt_util.datedeltastr(val)
                                elif col in LIST_FIELDS:
                                    val = '|'.join([str(_x) for _x in val])
                                row.append(val)
                                added = True
                                break
                            except AttributeError:
                                if col == 'type':
                                    row.append(entry.strip('s'))
                                    added = True
                        if not added:
                            row.append('')
                    writer.writerow(row)

