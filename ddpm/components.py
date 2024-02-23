from . import settings_proj as settings
from . import utils_ddp as ud
from . import utils_time as ut
import datetime
import hashlib
from copy import copy


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
            self._init_parameters()
            self._update_parameters(**kwargs)

    def __repr__(self):
        try:
            s = f"Name: {self.name}\n"
            for par in self.parameters:
                if par == 'name':
                    continue
                val = getattr(self, par)
                if par  == 'colinear':
                    val = 'No' if self.colinear is None else self.colinear.name
                elif par == 'predecessors':
                    val = 'No' if self.predecessors is None else ', '.join(x.name for x in self.predecessors)
                s += f"\t{par}: {val}\n"
            s += f"\tkey: {self.key}\n"
            return s
        except AttributeError:
            return "Blank Entry"

    def _init_parameters(self):
        """Set all parameters to None and initialize 'updated' attribute to now."""
        for par in self.parameters:
            setattr(self, par, None)
        self.updated = datetime.datetime.now().astimezone()
        self.timezone = copy(self.updated.tzinfo)

    def _update_parameters(self, **kwargs):
        """Update any parameter attributes with some baselevel checking."""
        if 'timezone' in kwargs:
            self.timezone = ut.datetimedelta(kwargs['timezone'], 'timezone')
            del(kwargs['timezone'])
        for key, val in kwargs.items():
            if key not in self.parameters:
                print(f"Invalid key '{key}' for {self.type}.")
                continue
            if key in settings.DATE_FIELDS:
                setattr(self, key, ut.datetimedelta(val, key, timezone=self.timezone))
            elif key in settings.LIST_FIELDS and isinstance(val, str):
                setattr(self, key, val.split(','))
            elif isinstance(val, str):
                setattr(self, key, val.strip())
            else:
                setattr(self, key, val)

        if 'note' in self.parameters:
            if self.note is None:
                self.note = []
            elif isinstance(self.note, str):
                self.note = [self.note]

        if 'color' in self.parameters:
            if isinstance(self.color, str) and self.color.startswith('('):
                self.color = [float(_x) for _x in self.color.strip('()').split(',')]
            if isinstance(self.color, str) and not len(self.color):
                self.color = 'k'

        try:
            self.status = float(self.status.strip('%'))
        except (ValueError, TypeError, AttributeError):
            pass
        if 'lag' in self.parameters:
            if self.lag is None:
                self.lag = datetime.timedelta(0)
            elif not isinstance(self.lag, datetime.timedelta):
                self.lag = datetime.timedelta(hours=float(self.lag))
        if 'complete' in self.parameters:
            try:
                self.complete = float(self.complete)
            except (ValueError, TypeError, AttributeError):
                pass
        print(f"Adding {self.type} {self.name}")

    def make_key(self, keystr):
        """Generate the unique hash key"""
        return hashlib.md5(keystr.encode('ascii')).hexdigest()[:6]

    def add_note(self, note):
        """Add a note string to the note list."""
        self.note.append(note)

    def get_color(self):
        print("Consolidate all of the get_color methods in the components below.")

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
                val = '|'.join([str(x).strip() for x in val])
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
        s = f"{self.type}{ctr} = ddp.{self.type.capitalize}({', '.join(kwlist)})\n"
        s += f"{projectname}.add_entry({self.type}{ctr})"
        return s


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
        note : list
            General note to add
        updated : str, datetime
            Date of the current update
        complete : str, float, None
            how late(=) or early (-) completed milestone was done - that is date is the actual and this tells how late/early that was
        predecessors : Entry, None
            list of predessors Entries, take latest
        lag : str, float, None
            how late to follow after last predecessor
        colinear : Entry, None
            Component entry to put on the same line
        marker : str
            Marker used for plotting
        color : str, None
            Color used for plotting, if None or 'auto' make based on status/lag

        """
        self.type = 'milestone'
        self.parameters = ['name', 'date', 'owner', 'label', 'status', 'note', 'updated', 'complete',
                           'predecessors', 'lag', 'groups', 'colinear', 'marker', 'color', 'timezone']
        kwargs.update({'name': name})
        if name is None:
            pass
        elif self.valid_request(**kwargs):
            super().__init__(**kwargs)
            if self.marker is None:
                self.marker = 'D'
            self.init_timing(kwargs)
            self.key = self.make_key(name + self.date.isoformat())
        else:
            print("Invalid Milestone request.")

    def init_timing(self, kwargs):
        provided_timing = set()
        for key in ['date', 'predecessors']:
            if key in kwargs and isinstance(getattr(self, key), (datetime.datetime, list)):
                provided_timing.add(key)
        if len(provided_timing) == 2:
            raise ValueError("Can't provide date and predecessors.")
        if not len(provided_timing):
            raise ValueError("Must provide one form of timing.")
        if provided_timing == {'predecessors'}:
            if self.lag is None:
                self.lag = datetime.timedelta(0)
            predecessor_times = []
            for pred in kwargs['predecessors']:
                predecessor_times.append(pred._predecessor_time)
            self.date = max(predecessor_times) + self.lag
        self._predecessor_time = self.date

    def valid_request(self, **kwargs):
        """Check info in a Milestone"""
        if 'duration' in kwargs and len(kwargs['duration'].strip()):
            return False
        if 'name' not in kwargs or not isinstance(kwargs['name'], str) or not len(kwargs['name'].strip()):
            return False
        if 'date' not in kwargs or not len(str(kwargs['date'])):
            return False
        return True

    # def __repr__(self):
    #     return f"{self.key}:  {self.name}  {self.date} "

    def get_color(self):
        now = datetime.datetime.now().astimezone()
        if self.color is None or self.color == 'auto':
            pass
        else:
            return self.color
        if self.status != 'complete' and now > self.date:
            return settings.STATUS_COLOR['late']
        if self.status == 'complete' and self.complete is not None:
            if abs(self.complete) > 1.0:
                return ud.complete2rgb(self.complete)
            return settings.STATUS_COLOR['complete']
        if self.status in settings.STATUS_COLOR:
            return settings.STATUS_COLOR[self.status]
        return settings.STATUS_COLOR['other']


class Timeline(Entry):
    tl_parameters = ['name', 'begins', 'ends', 'duration', 'note', 'updated', 'colinear',
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
            self.init_timing(kwargs)
            self.key = self.make_key(name + self.begins.isoformat() + self.ends.isoformat())
        else:
            print("Invalid Timeline request.")

    def init_timing(self, kwargs):
        # Check/get timing
        provided_timing = set()
        for key in ['begins', 'ends', 'duration', 'predecessors']:
            if key in kwargs and isinstance(getattr(self, key), (datetime.datetime, datetime.timedelta, list)):
                provided_timing.add(key)
        if provided_timing not in self.allowed_timing_sets:
            raise ValueError("Timing information not in allowed timing sets.")
        if 'predecessors' in provided_timing:
            if self.lag is None:
                self.lag = datetime.timedelta(0)
            predecessor_times = []
            for pred in kwargs['predecessors']:
                predecessor_times.append(pred._predecessor_time)
            self.begins = (max(predecessor_times) + self.lag).astimezone(self.timezone)
            provided_timing.add('begins')

        if 'duration' not in provided_timing:
            self.duration = self.ends - self.begins
        elif 'ends' not in provided_timing:
            self.ends = self.begins + self.duration
        elif 'begins' not in provided_timing:
            self.begins = self.ends - self.duration

        if self.begins > self.ends:
            print(f"Begins at: {self.begins} -- ends at:  {self.ends}")
            raise ValueError(f"{self.type} begins after ending")
        self._predecessor_time = self.ends

    def valid_request(self, **kwargs):
        return self._valid_request(**kwargs)

    def _valid_request(self, **kwargs):
        """Check info in a Timelineg"""
        if 'name' not in kwargs or not isinstance(kwargs['name'], str) or not len(kwargs['name'].strip()):
            return False
        provided_timing = set()
        for key in ['begins', 'ends', 'duration', 'predecessors']:
            if key in kwargs and len(str(kwargs[key])):
                provided_timing.add(key)
        if provided_timing not in self.allowed_timing_sets:
            return False
        return True

    # def __repr__(self):
    #     return f"{self.key}:  {self.name}  {self.begins} -  {self.ends}"

    def get_color(self):
        if self.color is None or self.color == 'auto':
            return ud.color_palette[0]
        return self.color

    def add_note(self, note):
        self.note.append(note)


class Task(Timeline):
    ta_extra = ['owner', 'status', 'complete']
    def __init__(self, name, **kwargs):
        self.parameters = copy(self.ta_extra)
        super().__init__(name=name, **kwargs)
        self.type = 'task'  # Overwrites 'timeline' type so is after super()

    def valid_request(self, **kwargs):  # This actually just differentiates Task or Timeline
        if self._valid_request(**kwargs):
            for par in self.ta_extra:
                if par in kwargs and isinstance(kwargs[par], (str, float, int)):
                    return True
        return False

    def get_color(self):
        if self.color is None or self.color == 'auto':
            if isinstance(self.status, float):
                now = datetime.datetime.now().astimezone()
                if int(self.status) != 100 and now > self.ends:
                    return settings.STATUS_COLOR['late']
                if self.begins > now:
                    return settings.color_palette[0]
                if self.complete is not None:
                    return ud.complete2rgb(self.complete)
                pc_elapsed = 100.0 * (now - self.begins) / self.duration
                completed = pc_elapsed - self.status if pc_elapsed > self.status else 0.0
                return ud.complete2rgb((completed-50.0))
            return settings.color_palette[0]
        return self.color


class Note(Entry):
    parameters = ['jot', 'date', 'reference', 'timezone']
    def __init__(self, jot, date='now', reference=None):
        self.type = 'note'
        if jot is None:  # Just want the parameters
            pass
        elif self.valid_request(jot=jot):
            self.date = ut.datetimedelta(date)
            self.jot = jot
            if reference is None:
                self.reference = []
            elif isinstance(reference, str):
                self.reference = reference.split(',')
            elif isinstance(reference, list):
                self.reference = reference
            else:
                print(f"Invalid reference {reference}")
            self.key = self.make_key(jot)
        else:
            print("Invalid Note request.")

    def valid_request(self, **kwargs):
        return True if 'jot' in kwargs and isinstance(kwargs['jot'], str) and len(kwargs['jot'].strip()) else False

    def add_reference(self, key):
        """
        Key of entry referenced by this note.
        """
        self.reference.append(key)