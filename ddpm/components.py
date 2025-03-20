from . import settings_proj as settings
from . import utils_proj as utils
from . import utils_time as ut
import datetime
import hashlib, logging
from copy import copy
from odsutils.ods_tools import listify


logger = logging.getLogger(__name__)  # Just get the logger


chart_types = ['task', 'milestone', 'timeline']
event_types = ['task', 'milestone']
other_types = ['timeline', 'note']


def components_dict():
    return {'entry': Entry(),
            'milestone': Milestone(None),
            'timeline': Timeline(None),
            'task':  Task(None),
            'note':  Note(None)}

class Entry:
    """
    Component Entry baseclass - it needs parameters to be set in child component.

    This baseclass has the small number of common methods across all components.  Each component gets a
    unique hash key, which is defined in a method here.

    """
    def __init__(self, **kwargs):
        """
        Initialize the component Entry baseclass.

        First sets all of the component parameters to None, and then updates them with supplied values.

        """
        if len(kwargs):
            self.init_parameters()
            self.update_parameters(**kwargs)

    def __str__(self):
        s = f"Name: {self.name}\n"
        for par in self.parameters:
            if par == 'name':
                continue
            try:
                val = getattr(self, par)
            except AttributeError:
                val = 'Not Present'
                continue
            s += f"\t{par}: {val}\n"
        s += f"\tkey: {self.key}\n"
        if hasattr(self, 'attrname'):
            s += f"\tattrname: {self.attrname}\n"
        else:
            s += f"\tattrname: None\n"
        return s

    def init_parameters(self):
        """Set all parameters to None and initialize 'updated' attribute to now."""
        for par in self.parameters:
            setattr(self, par, None)
        self.updated = datetime.datetime.now().astimezone()
        self.timezone = copy(self.updated.tzinfo)
        self.predecessor_data = []

    def set_lag(self):
        if 'lag' in self.parameters:
            if self.lag is None:
                self.lag = datetime.timedelta(0)
            elif not isinstance(self.lag, datetime.timedelta):
                self.lag = datetime.timedelta(days=float(self.lag))

    def update_parameters(self, **kwargs):
        """Update any parameter attributes with some baselevel checking."""
        if 'timezone' in kwargs:
            self.timezone = ut.datetimedelta(kwargs['timezone'], 'timezone')
            del(kwargs['timezone'])
        for key, val in kwargs.items():
            if key not in self.parameters:
                logger.error(f"Invalid key '{key}' for {self.type}.")
                continue
            if key in settings.DATE_FIELDS:
                setattr(self, key, ut.datetimedelta(val, key, timezone=self.timezone))
            elif key in settings.LIST_FIELDS and isinstance(val, str):
                setattr(self, key, val.split(','))
            elif isinstance(val, str):
                setattr(self, key, val.strip())
            else:
                setattr(self, key, val)
        if 'color' in self.parameters:
            if isinstance(self.color, str) and self.color.startswith('('):
                self.color = [float(_x) for _x in self.color.strip('()').split(',')]
            if isinstance(self.color, str) and not len(self.color):
                self.color = 'k'
        self.set_lag()
        if 'complete' in self.parameters:
            try:
                self.complete = float(self.complete)
            except (ValueError, TypeError, AttributeError):
                pass

    def make_key(self, params):
        """Generate the unique hash key"""
        ss = self.type + ''.join([str(getattr(self, par)) for par in params])
        return hashlib.md5(ss.encode('ascii')).hexdigest()[:6]

    def get_color(self):
        """
        This is a first attempt to gather the color stuff in one place.
        """
        if utils.is_color(self.color):
            return self.color
        if self.type in ['timeline', 'note']:
            return utils.COLOR_PALETTE[0]
        clrdate = self.date if self.type == 'milestone' else self.ends
        clrdate2 = None if self.type == 'milestone' else self.begins
        now = datetime.datetime.now().astimezone()
        if not isinstance(self.status, str):
            print(f"DDPM:component:123 -- non-string status {self.status}  ({type(self.status)})")
            return 'k'
        if self.status.lower() != 'complete':
            if clrdate2 is not None and clrdate2 > now:
                return settings.STATUS_COLOR['not_started']
            if now > clrdate:
                return settings.STATUS_COLOR['late']
            if self.status in settings.STATUS_COLOR:
                return settings.STATUS_COLOR[self.status]
            if clrdate2 is None:
                return settings.STATUS_COLOR['other']
            else:
                pc_elapsed = (now - clrdate2) / self.duration
                completed = pc_elapsed - self.complete if pc_elapsed > self.complete else 0.0
                return utils.complete2rgb(100.0*completed-50.0)
        else:
            if self.complete is not None and abs(self.complete) > 1.0:
                return utils.complete2rgb(self.complete)
            return settings.STATUS_COLOR['complete']

    def stringify(self):
        """
        Return a dictionary of the component parameters and their values.

        """
        d = {}
        for par in self.parameters:
            val = getattr(self, par)
            if par in settings.DATE_FIELDS:
                val = ut.datedeltastr(val)
            elif par in settings.LIST_FIELDS:
                val = ','.join([str(x).strip() for x in val])
            d[par] = val
        return d

    def gen_script_entry(self, ctr, projectname):
        """
        Take a component Entry and generate a python script line to implement it.

        Parameters
        ----------
        ctr : int
            Project supplied integer to provide a unique id.
        projectname : str
            Name of the project that is looking for this update script line.
        
        Return
        ------
        str
            A line of python text that would implement the component Entry

        """
        kwlist = []
        for par in self.parameters:
            val = getattr(self, par)
            if val is None or not len(str(val).strip()):
                continue
            if par in settings.DATE_FIELDS:
                val = ut.datedeltastr(val)
            elif par in settings.LIST_FIELDS:
                val = ','.join([str(x).strip() for x in val])
            else:
                try:
                    val = f"{float(val):.1f}"
                    val = val.split('.')[0] if val.endswith('.0') else val
                    is_num = True
                except ValueError:
                    val = str(val).strip()
                    is_num = False
            if len(str(val)):
                sp = '' if is_num else "'"
                kwlist.append(f"{par}={sp}{val}{sp}")
        s = f"{self.type}{ctr} = components.{self.type.capitalize()}({', '.join(kwlist)})\n"
        s += f"{projectname}.add_entry({self.type}{ctr})"
        return s

    def set_attrname(self, attrname):
        self.attrname = attrname

class Milestone(Entry):
    """
    """
    def __init__(self, name, **kwargs):
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
        updated : str, datetime
            Date of the current update
        complete : float, None
            Fraction complete (when < 1) or how early/late completed occurred in days from projected
        predecessors : Entry hash, None
            list of predessors Entries, take latest
        lag : str, float, None
            how late to follow after last predecessor
        colinear : Entry, None
            Component entry to put on the same line
        groups : list, None
            List of group names to associate with this milestone
        marker : str
            Marker used for plotting
        color : str, None
            Color used for plotting, if None or 'auto' make based on status/lag

        """
        self.type = 'milestone'
        self.parameters = ['name', 'date', 'owner', 'label', 'status', 'updated', 'complete',
                           'predecessors', 'lag', 'groups', 'colinear', 'marker', 'color', 'timezone']
        kwargs.update({'name': name})
        if name is None:
            pass
        elif self.valid_request(**kwargs):
            super().__init__(**kwargs)
            if self.marker is None:
                self.marker = 'D'
            self.key = self.make_key(['name', 'owner', 'label'])
        else:
            logger.error("Invalid Milestone request.")

    def set_timing(self):
        self.set_lag()
        if len(self.predecessor_data):
            self.date = max([x.date for x in self.predecessor_data]) + self.lag

    def valid_request(self, **kwargs):
        """Check info in a Milestone"""
        if 'name' not in kwargs or not isinstance(kwargs['name'], str) or not len(kwargs['name'].strip()):
            logger.error("Invalid Milestone request -- no name")
            return False
        if 'duration' in kwargs and len(kwargs['duration'].strip()):
            logger.debug("Provided duration for Milestone")
            return False
        ctrlist = [x for x in ['date', 'predecessors'] if x in kwargs and len(str(kwargs[x]))]
        if len(ctrlist) == 1:
            return True
        logger.debug(f"Invalid Milestone request -- need date or predecessors, provided {ctrlist}")
        return False


class Timeline(Entry):
    tl_parameters = ['name', 'begins', 'ends', 'owner', 'duration', 'updated', 'colinear',
                     'predecessors', 'lag', 'groups', 'label', 'color', 'timezone']
    allowed_timing_sets = [{'begins', 'ends'},
                           {'begins', 'duration'},
                           {'ends', 'duration'},
                           {'predecessors', 'duration'},
                           {'predecessors', 'ends'}]

    def __init__(self, name, **kwargs):
        self.type = 'timeline'
        try:  # Done this way to allow for the extra task parameters.
            self.parameters = self.tl_parameters + self.parameters
        except AttributeError:
            self.parameters = copy(self.tl_parameters)
        kwargs.update({'name': name})
        if name is None:
            pass
        elif self._valid_request(**kwargs):
            super().__init__(**kwargs)
            self.key = self.make_key(['name', 'owner', 'label'])
        else:
            logger.error("Invalid Timeline request.")

    def set_timing(self):
        self.set_lag()
        if len(self.predecessor_data):
            self.begins = max([x.ends for x in self.predecessor_data]) + self.lag
        if self.begins is None:
            self.begins = self.ends - self.duration
        elif self.ends is None:
            self.ends = self.begins + self.duration
        else:
            self.duration = self.ends - self.begins

    def valid_request(self, **kwargs):
        return self._valid_request(**kwargs)

    def _valid_request(self, **kwargs):
        """Check info in a Timeline"""
        if 'name' not in kwargs or not isinstance(kwargs['name'], str) or not len(kwargs['name'].strip()):
            logger.debug("Timeline valid_request: no name")
            return False
        provided_timing = set()
        for key in ['begins', 'ends', 'duration', 'predecessors']:
            if key in kwargs and len(str(kwargs[key])):
                provided_timing.add(key)
        if provided_timing not in self.allowed_timing_sets:
            logger.debug(f"Timeline valid_request: invalid timing set {provided_timing}")
            return False
        return True

class Task(Timeline):
    """
    A Task is just a Timeline with a status and a completion percentage.

    """
    ta_extra = ['status', 'complete']
    def __init__(self, name, **kwargs):
        self.parameters = copy(self.ta_extra)
        super().__init__(name=name, **kwargs)
        self.type = 'task'  # Overwrites 'timeline' type so is after super()
        if name is not None:
            self.key = self.make_key(['name', 'owner', 'label'])  # And annoyingly you have to do this again

    def valid_request(self, **kwargs):  # This actually just differentiates Task or Timeline (so just adds these)
        if self._valid_request(**kwargs):
            for par in self.ta_extra:
                if par in kwargs and isinstance(kwargs[par], (str, float, int)):
                    return True
        return False


class Note(Entry):
    def __init__(self, jot, **kwargs):
        self.type = 'note'
        self.parameters = ['jot', 'date', 'reference', 'timezone']
        kwargs.update({'jot': jot})
        if jot is None:  # Just want the parameters
            pass
        elif self.valid_request(**kwargs):
            super().__init__(**kwargs)
            self.reference = listify(self.reference)
            self.key = self.make_key(['jot', 'reference'])
        else:
            logger.error("Invalid Note request.")

    def valid_request(self, **kwargs):
        return True if 'jot' in kwargs and isinstance(kwargs['jot'], str) and len(kwargs['jot'].strip()) else False

    def set_timing(self):
        self.date = ut.datetimedelta('now') if self.date is None else self.date

    def add_reference(self, key):
        """
        Key of entry referenced by this note.
        """
        self.reference.append(key)