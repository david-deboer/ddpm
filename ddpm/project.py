from copy import copy
from . import plots_proj as plots
from . import settings_proj as settings
from . import utils_proj as utils
from . import utils_time as ut
from . import components
from odsutils import logger_setup
import datetime
from argparse import Namespace
import csv
import logging


logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')  # Set to lowest
from . import LOG_FILENAME, LOG_FORMATS, __version__


class Project:
    """
    This is a collection of components (components.py) and handles them as an aggregate.
    """

    def __init__(self, name, organization=None, timezone=None, conlog='INFO', filelog=False):
        """
        Parameters
        ----------
        name : str
            Name of project (heading)
        organization : str, None
            Name of organization
        timezone : interpretable as ut.datetimedelta.timezone, None
            Preferred timezone

        Attributes
        ----------
        self.all_entries : dict
            copy of the component entry
        self.colinear_map : dict
            keep track of Gantt chart colinear entries
        self.earliest : dict
            earliest date per component type
        self.latest : dict
            latest date per component type
        self.updated : datetime, None
            updated datetime
        self.timezone : same as Parameter
        self.listed_component_names : list
            if a preferred attribute name is passed, gets added to this list as well
                   
        """
        self.log_settings = logger_setup.Logger(logger, conlog=conlog, filelog=filelog, log_filename=LOG_FILENAME, path=None,
                                                conlog_format=LOG_FORMATS['conlog_format'], filelog_format=LOG_FORMATS['filelog_format'])
        logger.info(f"{__name__} ver. {__version__}")
        self.entry_types = components.event_types + components.other_types
        self.name = name
        self.organization = organization
        self.all_entries = {}
        for entry_type in self.entry_types:
            setattr(self, f"{entry_type}s", [])
        self.colinear_map = {}
        self.earliest, self.latest = {}, {}
        self.updated = None
        self.timezone = ut.datetimedelta(timezone, 'timezone')
        self.listed_component_names = []
        for entry in self.entry_types:
            self.earliest[entry] = None
            self.latest[entry] = None

    def __str__(self):
        extrema = self.get_event_extrema()
        if extrema.min is None or extrema.max is None:
            duration = 'No entries'
        else:
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

    def add(self, entry, attrname=None):
        """
        Parameters
        ----------
        entry : component instance
            see components.py
        attrname : str or None
            if str, will make a project attribute of that name and add to self.listed_component_names

        """
        try:
            if entry.key in self.all_entries.keys():
                logger.error(f"Warning - not adding '{entry.type}': Key for {entry.name} already used ({entry.key}).")
                return
        except AttributeError:
            return
        self.all_entries[entry.key] = copy(entry)

        try:
            if entry.colinear is not None:
                self.colinear_map[entry.key] = entry.colinear.key
        except AttributeError:
            pass
        getattr(self, f"{entry.type}s").append(entry.key)
        if attrname is not None:
            entry.set_attrname(attrname)
            setattr(self, attrname, copy(entry))
            self.listed_component_names.append(attrname)

    def sort(self, entry_types, sortby):
        if entry_types == 'all':
            entry_types = components.chart_types
        elif isinstance(entry_types, str):
            entry_types = [entry_types]

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

    def postproc(self):
        """
        Go through all entries and pull predecessor data into components and set timing

        """
        for key in self.all_entries.keys():
            this = self.all_entries[key]
            if this.type == 'note':
                continue
            if this.predecessors is not None and len(this.predecessors):
                for pred in this.predecessors:
                    try:
                        self.all_entries[key].predecessor_data.append(self.all_entries[pred])
                    except KeyError:
                        logger.error(f"Warning - predecessor {pred} not found for {this.name} ({this.key}).")
        for key in self.all_entries.keys():
            this = self.all_entries[key]
            this.set_timing()
            early_date = this.date if this.type == 'milestone' else this.begins
            late_date = this.date if this.type == 'milestone' else this.ends
            if self.earliest[this.type] is None or early_date < self.earliest[this.type]:
                self.earliest[this.type] = early_date
            if self.latest[this.type] is None or late_date > self.latest[this.type]:
                self.latest[this.type] = late_date

    def align_keys(self, ykeys):
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

    def get_event_extrema(self):
        chkmin, chkmax = [], []
        for event in components.chart_types:
            if self.earliest[event] is not None:
                chkmin.append(self.earliest[event])
            if self.latest[event] is not None:
                chkmax.append(self.latest[event])
        chkmin = None if not len(chkmin) else min(chkmin)
        chkmax = None if not len(chkmax) else max(chkmax)
        return Namespace(min=chkmin, max=chkmax)

    def list(self, chart='all', sortby=['begins', 'date', 'name', 'ends']):
        for sortkey in self.sort(chart, sortby):
            print(self.all_entries[sortkey])

    def chart(self, chart='all', sortby=['begins', 'date', 'name', 'ends'], **kwargs):

        """
        Make a gantt chart.

        Parameter
        ---------
        chart : str or list
              'all' for all chart_types, or a list of chart_types (groups)
        sortby : list or 'all' (chart_types)
           fields to sort by
        kwargs parameters see settings_proj.CHART_DEFAULTS

        """
        kwargs2use = copy(settings.CHART_DEFAULTS)
        kwargs2use.update(copy(kwargs))

        self.gantt = plots.Gantt(name = self.name)
        dates = []
        labels = []
        plotpars = []
        ykeys = []  # keys lists the keys used, used to make the vertical axis including colinear

        extrema = self.get_event_extrema()
        if extrema.min is None or extrema.max is None:
            logger.warning("No entries.")
            return
        duration = extrema.max - extrema.min

        logger.info(f"Duration = {ut.pretty_duration(duration.total_seconds())}")
        for sortkey in self.sort(chart, sortby):
            this = self.all_entries[sortkey]
            if this.type == 'milestone':
                dates.append([copy(this.date).astimezone(self.timezone), None])
                plotpars.append(Namespace(color=this.get_color(), marker=this.marker, status=None, owner=this.owner))
            elif this.type == 'timeline':
                dates.append([copy(this.begins).astimezone(self.timezone), copy(this.ends).astimezone(self.timezone)])
                plotpars.append(Namespace(color=this.get_color(), status=None, owner=None))
            elif this.type == 'task':
                dates.append([copy(this.begins).astimezone(self.timezone), copy(this.ends).astimezone(self.timezone)])
                plotpars.append(Namespace(color=this.get_color(), status=this.status, owner=this.owner))
            if this.label is not None:
                labels.append(this.label)
            else:
                labels.append(this.name)
            ykeys.append(this.key)
        ykeys = self.align_keys(ykeys)
        self.gantt.setup(dates=dates, info=plotpars, labels=labels, ykeys=ykeys, extrema=extrema, timezone=self.timezone)
        self.gantt.chart(**kwargs2use)

    def cumulative(self, step=1.0, show=True):
        """
        Make a cumulative milestone chart.

        Parameter
        ---------
        sortby : list
           fields to sort by, must be unique.  sort_info dicts map if needed
        """
        extrema = self.get_event_extrema()
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
                if this_date > dates[i] and self.eval_status_complete(status[i]):
                    ctr += 1.0
            self.cdf.values.append(ctr)
            this_date += datetime.timedelta(days=step)
        if self.cdf.dates[-1] != extrema.max:
            self.cdf.dates.append(extrema.max)
            ctr = 0.0
            for i in range(len(status)):
                if self.eval_status_complete(status[i]):
                    ctr += 1.0
            self.cdf.values.append(ctr)
        if show:
            plots.cumulative_graph(self.cdf.dates, self.cdf.values, len(dates))

    def eval_status_complete(self, status):
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
        sorted_keys = self.sort(['note'], sortby)
        for sortkey in sorted_keys:
            this = self.all_entries[sortkey]
            print(f"{this.jot}  {this.date.strftime('%Y-%m-%d %H:%M')}  - ({', '.join(this.reference)})")

    def color_bar(self):
        utils.color_bar()

    def determine_entry_type(self, header, row):
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

    def preproc_csv(self, hdr, val):
        """
        Do more later, e.g. check if val=='none' and return None etc...

        """
        if isinstance(val, str):  # Should _always_ be a str
            val = val.strip()
            if not len(val):
                return val
        else:
            logger.warning(f"Information:  {val} is not a str ({hdr}) - do I care?")
        if hdr == 'colinear':
            if val.startswith('#'):
                val = val.strip('#')
            else:
                val = self.empty_classes['entry'].make_key(val)
        return val

    def csvread(self, loc):
        fp = None
        logger.info(f"Reading {loc}")
        self.empty_classes = components.components_dict()  # defined in components.py
        classdecl = {'milestone': components.Milestone, 'timeline': components.Timeline, 'task': components.Task}

        if loc.startswith('http'):
            data = utils.load_sheet_from_url(loc)
            header = copy(data[0])
            reader = data[1:]
        else:
            fp = open(loc, 'r')
            reader = csv.reader(fp)
            header = next(reader)
        
        for row in reader:
            entry_type = self.determine_entry_type(header, row)
            if not entry_type:
                logger.error(f"No valid entry_type:  {row[0]}")
                continue
            kwargs = {}
            for hdrc, val in zip(header, row):
                if not len(val.strip()):
                    continue
                for hdr in hdrc.split(':'):
                    found_valid = False
                    if hdr.strip() in self.empty_classes[entry_type].parameters:
                        found_valid = True
                        kwargs[hdr] = self.preproc_csv(hdr, val)
                        break
                if not found_valid:
                    logger.error(f"No valid component:  {entry_type} -- {row}")
            if self.empty_classes[entry_type].valid_request(**kwargs):
                logger.info(f'Adding {entry_type}  {row[0]}')
                if entry_type == 'note':
                    jot = copy(kwargs['jot'])
                    del kwargs['jot']
                    this = components.Note(jot=jot, **kwargs)
                else:
                    name = copy(kwargs['name'])
                    del kwargs['name']
                    this = classdecl[entry_type](name=name, **kwargs)
                self.add(this)
            else:
                logger.warning(f"Skipping invalid {entry_type}:  {row}.")
        if fp is not None:
            fp.close()
        self.postproc()

    def export_script(self, fn='export_script.py', projectname='project'):
        """
        This will write out the project to a python script.

        """
        logger.info(f"Writing {fn}")
        ctr = {}
        with open(fn, 'w') as fp:
            print("from ddpm import project, components\n", file=fp)
            org = '' if self.organization is None else f", organization='{self.organization}'"
            print(f"{projectname} = project.Project('{self.name}'{org})\n", file=fp)
            for entry in self.all_entries.values():
                ctr.setdefault(entry.type, 0)
                print(entry.gen_script_entry(ctr[entry.type], projectname), file=fp)
                ctr[entry.type] += 1

    def update_archive(self, archive_fn='tracking.json'):
        """
        This will write out the project to a json file.

        """
        import json
        self.archive_fn = archive_fn
        with open(archive_fn, 'r') as fp:
            self.archive = json.load(fp)
        arcent = {}
        for key, val in self.all_entries.items():
            if val.status == 'complete':
                key = f"{key}_{datetime.now.isoformat()}_{val.complete}"
            arcent[key] = val.stringify()
        self.archive.update(arcent)
        logger.info(f"Writing {archive_fn}")
        with open(self.archive_fn, 'w') as fp:
            json.dump(self.archive, fp, indent=2)

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

        entpar = utils.components_parameters(show=False)
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
        print("CSV write not implemented")
        return
        logger.info(f"Writing csv file {fn}")
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
                                elif col in utils.DATE_FIELDS:
                                    val = utils.datedeltastr(val)
                                elif col in utils.LIST_FIELDS:
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

