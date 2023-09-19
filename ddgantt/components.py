from . import gantt_util as gu
import datetime
import hashlib
from copy import copy


class Entry:
    def __init__(self, **kwargs):
        # Set parameter defaults to None
        if len(kwargs):
            self._init_parameters()
            self._update_parameters(**kwargs)

    def __repr__(self):
        try:
            s = f"key: {self.key}\n"
            for par in self.parameters:
                s += f"\t{par}: {getattr(self, par)}\n"
            return s
        except AttributeError:
            return "Blank Entry"

    def _init_parameters(self):
        for par in self.parameters:
            setattr(self, par, None)
        self.updated = gu.datetimedelta('now')

    def _update_parameters(self, **kwargs):
        # Update parameters
        for key, val in kwargs.items():
            if key not in self.parameters:
                print(f"Invalid key '{key}' for {self.type}.")
                continue
            if key in gu.DATE_FIELDS:
                setattr(self, key, gu.datetimedelta(val, key))
            elif key in gu.LIST_FIELDS and isinstance(val, str):
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
                self.lag = 0.0
            else:
                try:
                    self.lag = float(self.lag)
                except (ValueError, TypeError, AttributeError):
                    pass
        if 'complete' in self.parameters:
            try:
                self.complete = float(self.complete)
            except (ValueError, TypeError, AttributeError):
                pass

    def make_key(self, keystr):
        return hashlib.md5(keystr.encode('ascii')).hexdigest()[:6]

    def add_note(self, note):
        self.note.append(note)

    def gen_script_entry(self, entrytype, entryname, projectname):
        kwlist = []
        for par in self.parameters:
            val = getattr(self, par)
            if val is None or not len(str(val).strip()):
                continue
            if par in gu.DATE_FIELDS:
                val = gu.datedeltastr(val)
            elif par in gu.LIST_FIELDS:
                val = '|'.join([str(x).strip() for x in val])
            else:
                try:
                    val = f"{float(val):.1f}"
                    val = val.split('.')[0] if val.endswith('.0') else val
                except ValueError:
                    val = str(val).strip()
            if len(val):
                sp = ',' if ' ' in val else ''
                kwlist.append(f"{par}={sp}{val}{sp}")
        s = f"{entryname} = gantt.{entrytype}({', '.join(kwlist)})\n"
        s += f"{projectname}.add_{entrytype.lower()}({entryname})"
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
        lag : str, float, None
            how late to follow after last predecessor
        colinear : str, None
            Key of other milestone to put on the same line
        marker : str
            Marker used for plotting
        color : str, None
            Color used for plotting, if None or 'auto' make based on status/lag
        """
        self.type = 'milestone'
        self.parameters = ['name', 'date', 'owner', 'label', 'status', 'note', 'updated', 'complete',
                           'predecessors', 'lag', 'groups', 'colinear', 'marker', 'color']
        kwargs.update({'name': name})
        if name is None:
            pass
        elif self.valid_request(**kwargs):
            super().__init__(**kwargs)
            if self.marker is None:
                self.marker = 'D'
            self.key = self.make_key(name)
            self.init_timing(kwargs)
        else:
            print("Invalid Milestone request.")

    def init_timing(self, kwargs):
        self.predecessor_timing = False
        provided_timing = set()
        for key in ['date', 'predecessors']:
            if key in kwargs and isinstance(getattr(self, key), (datetime.datetime, list)):
                provided_timing.add(key)
        if len(provided_timing) == 2:
            raise ValueError("Can't provide date and predecessors.")
        if not len(provided_timing):
            raise ValueError("Must provide one form of timing.")
        if provided_timing == {'predecessors'}:
            self.predecessor_timing = True  # This flag will be looked for later in ddproject

    def valid_request(self, **kwargs):
        if 'duration' in kwargs and len(kwargs['duration'].strip()):
            return False
        if 'name' not in kwargs or not isinstance(kwargs['name'], str) or not len(kwargs['name'].strip()):
            return False
        timing = 0
        for par in ['date', 'predecessors']:
            if par in kwargs:
                if isinstance(kwargs[par], str) and len(kwargs[par].strip()):
                    timing += 1
                elif isinstance(kwargs[par], (datetime.datetime, list)):
                    timing += 1
        return True if timing == 1 else False

    def set_predecessor_timing(self, timing):
        self.date = max(timing) + datetime.timedelta(days=self.lag)

    # def __repr__(self):
    #     return f"{self.key}:  {self.name}  {self.date} "

    def get_color(self):
        if self.color is None or self.color == 'auto':
            pass
        else:
            return self.color
        if self.status != 'complete' and datetime.datetime.now() > self.date:
            return gu.STATUS_COLOR['late']
        if self.status == 'complete' and self.complete is not None:
            if abs(self.complete) > 1.0:
                return gu.complete2rgb(self.complete)
            return gu.STATUS_COLOR['complete']
        if self.status in gu.STATUS_COLOR:
            return gu.STATUS_COLOR[self.status]
        return gu.STATUS_COLOR['other']


class Timeline(Entry):
    tl_parameters = ['name', 'begins', 'ends', 'duration', 'note', 'updated', 'colinear',
                     'predecessors', 'lag', 'groups', 'label', 'color']
    allowed_timing_sets = [{'begins', 'ends'},
                           {'begins', 'duration'},
                           {'ends', 'duration'},
                           {'predecessors', 'duration'}]

    def __init__(self, name, **kwargs):
        self.type = 'timeline'
        try:
            self.parameters = self.tl_parameters + self.parameters
        except AttributeError:
            self.parameters = copy(self.tl_parameters)
        kwargs.update({'name': name})
        if name is None:
            pass
        elif self._valid_request(**kwargs):
            super().__init__(**kwargs)
            self.key = self.make_key(name)
            self.init_timing(kwargs)
        else:
            print("Invalid Timeline request.")

    def init_timing(self, kwargs):
        # Check/get timing
        self.predecessor_timing = False
        provided_timing = set()
        for key in ['begins', 'ends', 'duration', 'predecessors']:
            if key in kwargs and isinstance(getattr(self, key), (datetime.datetime, datetime.timedelta, list)):
                provided_timing.add(key)
        if provided_timing not in self.allowed_timing_sets:
            raise ValueError("Timing information not in allowed timing sets.")
        if provided_timing == {'predecessors', 'duration'}:
            self.predecessor_timing = True  # This flag will be looked for later in project
        else:
            if 'duration' not in provided_timing:
                self.duration = self.ends - self.begins
            elif 'ends' not in provided_timing:
                self.ends = self.begins + self.duration
            elif 'begins' not in provided_timing:
                self.begins = self.ends - self.duration

    def valid_request(self, **kwargs):
        return self._valid_request(**kwargs)

    def _valid_request(self, **kwargs):
        if 'name' not in kwargs or not isinstance(kwargs['name'], str) or not len(kwargs['name'].strip()):
            return False
        provided_timing = set()
        for par in ['begins', 'ends', 'duration', 'predecessors']:
            if par in kwargs:
                if isinstance(kwargs[par], str) and len(kwargs[par].strip()):
                    provided_timing.add(par)
                elif isinstance(kwargs[par], (datetime.datetime, datetime.timedelta, list)):
                    provided_timing.add(par)
        return True if provided_timing in self.allowed_timing_sets else False

    def set_predecessor_timing(self, timing):
        self.begins = max(timing) + datetime.timedelta(days=self.lag)
        self.ends = self.begins + self.duration

    # def __repr__(self):
    #     return f"{self.key}:  {self.name}  {self.begins} -  {self.ends}"

    def get_color(self):
        if self.color is None or self.color == 'auto':
            return gu.color_palette[0]
        return self.color

    def add_note(self, note):
        self.note.append(note)


class Task(Timeline):
    ta_extra = ['owner', 'status', 'complete']
    def __init__(self, name, **kwargs):
        self.parameters = copy(self.ta_extra)
        super().__init__(name=name, **kwargs)
        self.type = 'task'

    def valid_request(self, **kwargs):  # This actually just differentiates Task or Timeline
        if self._valid_request(**kwargs):
            for par in self.ta_extra:
                if par in kwargs and isinstance(kwargs[par], (str, float, int)):
                    return True
        return False

    def get_color(self):
        if self.color is None or self.color == 'auto':
            if isinstance(self.status, float):
                now = datetime.datetime.now()
                if int(self.status) != 100 and now > self.ends:
                    return gu.STATUS_COLOR['late']
                if self.begins > now:
                    return gu.color_palette[0]
                if self.complete is not None:
                    return gu.complete2rgb(self.complete)
                pc_elapsed = 100.0 * (now - self.begins) / self.duration
                completed = pc_elapsed - self.status if pc_elapsed > self.status else 0.0
                return gu.complete2rgb((completed-50.0))
            return gu.color_palette[0]
        return self.color


class Note(Entry):
    parameters = ['jot', 'date', 'reference']
    def __init__(self, jot, date='now', reference=None):
        self.type = 'note'
        if jot is None:  # Just want the parameters
            pass
        elif self.valid_request(jot=jot):
            self.date = gu.datetimedelta(date)
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