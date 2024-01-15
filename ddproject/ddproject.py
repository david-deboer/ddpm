from copy import copy
from . import plotting
from . import util
from . import components
import datetime
from argparse import Namespace
import csv


class Project:
    """
    This is a collection of components (components.py) and handles them as an aggregate.
    """

    def __init__(self, name, organization=None):
        self.entry_types = components.event_types + components.other_types
        self.name = name
        self.organization = organization
        self.all_entries = {}
        for entry_type in self.entry_types:
            setattr(self, f"{entry_type}s", [])
        self.colinear_map = {}
        self.earliest, self.latest = {}, {}
        self.updated = None
        self.timezone = None
        for entry in self.entry_types:
            self.earliest[entry] = None
            self.latest[entry] = None

    def __repr__(self):
        extrema = self._get_event_extrema()
        duration = extrema.max - extrema.min
        s = f"Project:  {self.name}\n"
        if self.organization is not None:
            s += f"Organization: {self.organization}\n"
        s += f"{extrema.min} - {extrema.max}  ({duration})\n"
        tot = 0
        for et in self.entry_types:
            n = len(getattr(self, f"{et}s"))
            if n:
                pr = '' if n == 1 else 's'
                s += f"{n:03d} {et.capitalize()}{pr}\n"
                tot += n
        s +=  "-----------------\n"
        s += f"{tot:03d} Total Entries\n"
        return s

    def add(self, entry):
        try:
            if entry.key in self.all_entries.keys():
                print(f"Warning - not adding '{entry.type}': Key for {entry.name} already used ({entry.key}).")
                return
        except AttributeError:
            return
        self.all_entries[entry.key] = copy(entry)
        if entry.type in ['milestone', 'note']:
            early_date = copy(entry.date)
            late_date = copy(entry.date)
        else:
            early_date = copy(entry.begins)
            late_date = copy(entry.ends)
        if self.earliest[entry.type] is None:
            self.earliest[entry.type] = early_date
        elif early_date < self.earliest[entry.type]:
            self.earliest[entry.type] = early_date
        if self.latest[entry.type] is None:
            self.latest[entry.type] = late_date
        elif late_date > self.latest[entry.type]:
            self.latest[entry.type] = late_date
        try:
            if entry.colinear is not None:
                self.colinear_map[entry.key] = entry.colinear.key
        except AttributeError:
            pass
        getattr(self, f"{entry.type}s").append(entry.key)
        if entry.timezone is not None and entry.timezone != self.timezone:
            if self.timezone is None:
                _tz = 'None'
            else:
                _tz = self.timezone.tzname(None)
            print(f"Changing timezone from {_tz} to {entry.timezone.tzname(None)}")
            self.timezone = entry.timezone

    def _sort_(self, entry_types, sortby):
        sort_key_dict = {}
        for entry_type in entry_types:
            for key in getattr(self, f"{entry_type}s"):
                this = self.all_entries[key]
                skey = ''
                for upar in sortby:
                    try:
                        skey += str(getattr(this, upar)) + '_'
                    except AttributeError:
                        continue
                skey += f"{key}"  # To make sure unique
                sort_key_dict[skey] = this.key
        sorted_keys = []
        for skey in sorted(sort_key_dict.keys()):
            sorted_keys.append(sort_key_dict[skey])
        return sorted_keys

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
        for event in components.chart_types:
            if self.earliest[event] is not None:
                chkmin.append(self.earliest[event])
            if self.latest[event] is not None:
                chkmax.append(self.latest[event])
        chkmin = None if not len(chkmin) else min(chkmin)
        chkmax = None if not len(chkmax) else max(chkmax)
        return Namespace(min=chkmin, max=chkmax)

    def chart(self, chart='all', sortby=['begins', 'date', 'name', 'ends'], interval=None, grid=False,
              colinear_delimiter='|', weekends=True, months=True):
        """
        Make a gantt chart.

        Parameter
        ---------
        sortby : list or 'all' (chart_types)
           fields to sort by
        """
        self.gantt = plotting.Gantt(name = self.name)
        if chart == 'all':
            chart = components.chart_types
        elif isinstance(chart, str):
            chart = [chart]
        dates = []
        labels = []
        plotpars = []
        ykeys = []  # keys lists the keys used, used to make the vertical axis including colinear

        extrema = self._get_event_extrema()
        if extrema.min is None or extrema.max is None:
            print("No entries.")
            return
        duration = extrema.max - extrema.min

        print(f"Duration = {util.pretty_duration(duration.total_seconds())}")
        for sortkey in self._sort_(chart, sortby):
            this = self.all_entries[sortkey]
            if this.type == 'milestone':
                dates.append([this.date, None])
                plotpars.append(Namespace(color=this.get_color(), marker=this.marker, owner=this.owner))
            elif this.type == 'timeline':
                dates.append([this.begins, this.ends])
                plotpars.append(Namespace(color=this.get_color(), status=None, owner=None))
            elif this.type == 'task':
                dates.append([this.begins, this.ends])
                plotpars.append(Namespace(color=this.get_color(), status=this.status, owner=this.owner))
            if this.label is not None:
                labels.append(this.label)
            else:
                labels.append(this.name)
            ykeys.append(this.key)
        ykeys = self._align_keys(ykeys)
        self.gantt.setup(dates=dates, plotpars=plotpars, labels=labels, ykeys=ykeys, extrema=extrema, timezone=self.timezone)
        self.gantt.chart(interval=interval, grid=grid, colinear_delimiter=colinear_delimiter, weekends=weekends, months=months)

    def cumulative(self, step=1.0, show=True):
        """
        Make a cumulative milestone chart.

        Parameter
        ---------
        sortby : list
           fields to sort by, must be unique.  sort_info dicts map if needed
        """
        extrema = self._get_event_extrema()
        dates, status = [], []
        for key in self.milestones + self.tasks:
            this = self.all_entries[key]
            dates.append(this.date if this.type == 'milestone' else this.ends)
            status.append(Namespace(status=this.status, type=this.type))
        self.cdf = Namespace(dates=[], values=[])
        this_date = copy(extrema.min)
        while this_date < extrema.max:
            self.cdf.dates.append(this_date)
            ctr = 0.0
            for i in range(len(dates)):
                if this_date > dates[i] and self._eval_status_complete(status[i]):
                    ctr += 1.0
            self.cdf.values.append(ctr)
            this_date += datetime.timedelta(days=step)
        if self.cdf.dates[-1] != extrema.max:
            self.cdf.dates.append(extrema.max)
            ctr = 0.0
            for i in range(len(status)):
                if self._eval_status_complete(status[i]):
                    ctr += 1.0
            self.cdf.values.append(ctr)
        if show:
            plotting.cumulative_graph(self.cdf.dates, self.cdf.values, len(dates))

    def _eval_status_complete(self, status):
        if isinstance(status.status, str) and status.status.lower() == 'complete':
            return True
        try:
            score = int(status.status)
        except (TypeError, ValueError):
            score = False
        if score == 100:
            return True
        return False

    def show_notes(self, sortby=['date', 'jot']):
        sorted_keys = self._sort_(['note'], sortby)
        for sortkey in sorted_keys:
            this = self.all_entries[sortkey]
            print(f"{this.jot}  {this.date.strftime('%Y-%m-%d %H:%M')}  - ({', '.join(this.reference)})")

    def color_bar(self):
        util.color_bar()

    def _determine_entry_type(self, header, row):
        kwargs = {}
        for hdr, r in zip(header, row):
            if len(hdr.strip()):
                for h in hdr.split(':'):
                    kwargs[h.strip()] = r.strip()
        if 'type' in kwargs:
            if isinstance(kwargs['type'], str) and kwargs['type'].lower() in self.entry_types:
                return kwargs['type']
        for trial in ['task', 'timeline', 'milestone', 'note']:
            if self.empty_classes[trial].valid_request(**kwargs):
                return trial
        return False

    def _preproc_val(self, hdr, val):
        """
        Do more later, e.g. check if val=='none' and return None etc...

        """
        if isinstance(val, str):  # Should _always_ be a str
            val = val.strip()
            if not len(val):
                return val
        else:
            print(f"Information:  {val} is not a str ({hdr}) - do I care?")
        if hdr == 'colinear':
            if val.startswith('#'):
                val = val.strip('#')
            else:
                val = self.empty_classes['entry'].make_key(val)
        return val

    def csvread(self, loc, verbose=False):
        fp = None
        print(f"Reading {loc}")
        self.empty_classes = components.components_dict()  # defined in components.py
        classdecl = {'milestone': components.Milestone, 'timeline': components.Timeline, 'task': components.Task}

        if loc.startswith('http'):
            data = util.load_sheet_from_url(loc)
            header = copy(data[0])
            reader = data[1:]
        else:
            fp = open(loc, 'r')
            reader = csv.reader(fp)
            header = next(reader)
        
        for row in reader:
            entry_type = self._determine_entry_type(header, row)
            if not entry_type:
                print(f"No valid entry_type:  {row}")
                continue
            kwargs = {}
            for hdrc, val in zip(header, row):
                if not len(val.strip()):
                    continue
                for hdr in hdrc.split(':'):
                    found_valid = False
                    if hdr.strip() in self.empty_classes[entry_type].parameters:
                        found_valid = True
                        kwargs[hdr] = self._preproc_val(hdr, val)
                        break
                if not found_valid:
                    print(f"No valid component:  {entry_type} -- {row}")
            if self.empty_classes[entry_type].valid_request(**kwargs):
                if verbose:
                    print(f'Adding {entry_type}  {row}')
                if entry_type == 'note':
                    jot = copy(kwargs['jot'])
                    del kwargs['jot']
                    this = components.Note(jot=jot, **kwargs)
                else:
                    name = copy(kwargs['name'])
                    del kwargs['name']
                    this = classdecl[entry_type](name=name, **kwargs)
                self.add_entry(this)
            elif verbose:
                print(f"Skipping invalid {entry_type}:  {row}.")
        if fp is not None:
            fp.close()

    def scriptwrite(self, fn='export_script.py', projectname='project'):
        """
        This will write out the project to a python script.
        """
        print(f"Writing {fn}")
        ctr = {}
        with open(fn, 'w') as fp:
            print("from ddgantt import ddproject as ddp\n", file=fp)
            org = '' if self.organization is None else f", organization='{self.organization}'"
            print(f"{projectname} = gantt.Project('{self.name}'{org})\n", file=fp)
            for entry in self.all_entries.values():
                ctr[entry.type].setdefault(1)
                print(entry.gen_script_entry(ctr[entry.type], projectname), file=fp)
                ctr[entry.type] += 1

    def _get_csv_col(self, paired_col):
        """Done ugly to get the complete and unique column headers."""
        cols = []
        trackcol = set()
        pcdict = {}
        for pcol in paired_col:
            col2 = pcol.split(':')
            pcdict[col2[0]] = col2[1]
            pcdict[col2[1]] = col2[0]
            pcdict[f"v{col2[0]}"] = pcol
            pcdict[f"v{col2[1]}"] = pcol

        entpar = util.components_parameters(show=False)
        for entry in self.entry_types:
            for p in entpar[entry]:
                if p in pcdict:
                    trackcol.add(pcdict[p])
                if p not in trackcol:
                    if p in pcdict:
                        cols.append(pcdict[f'v{p}'])
                    else:
                        cols.append(p)
                trackcol.add(p)
#        cols = ['name', 'begins:date', 'ends', 'duration', 'colinear', 'color', 'status', 'groups', 'label',
#                'complete', 'marker', 'note:jot', 'owner', 'predecessors:reference', 'updated', 'type', 'key']
        return cols

    def csvwrite(self, fn, paired_col=['begins:date', 'note:jot', 'predecessors:reference']):
        print(f"Writing csv file {fn}")
        ccols = self._get_csv_col(paired_col=paired_col)
        return ccols
        with open(fn, 'w') as fp:
            writer = csv.writer(fp)
            writer.writerow(ccols)
            for entry in ['milestones', 'timelines', 'tasks', 'notes']:
                for this in getattr(self, entry).values():
                    row = []
                    for cols in ccols:
                        added = False
                        for col in cols.split(':'):
                            try:
                                val = getattr(this, col)
                                if val is None:
                                    val = ''
                                elif col in util.DATE_FIELDS:
                                    val = util.datedeltastr(val)
                                elif col in util.LIST_FIELDS:
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

