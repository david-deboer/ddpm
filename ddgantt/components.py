from . import gantt_util as gu
import datetime
import hashlib


class Entry:
    def __init__(self, name, **kwargs):
        # Set parameter defaults to None
        for par in self.parameters:
            setattr(self, par, None)
        self.updated = gu.datetimedelta('now')

        # Update parameters
        self.name = name
        for key, val in kwargs.items():
            if key not in self.parameters:
                print(f"Invalid key {key} in {self.name}")
                continue
            if key in gu.DATE_FIELDS:
                setattr(self, key, gu.datetimedelta(val, key))
            elif key in gu.LIST_FIELDS and isinstance(val, str):
                setattr(self, key, val.split(','))
            else:
                setattr(self, key, val)

        if self.note is None:
            self.note = []
        elif isinstance(self.note, str):
            self.note = [self.note]

        if isinstance(self.color, str) and self.color.startswith('('):
            self.color = [float(_x) for _x in self.color.strip('()').split(',')]
        if isinstance(self.color, str) and not len(self.color):
            self.color = 'k'

        try:
            self.status = float(self.status.strip('%'))
        except (ValueError, TypeError, AttributeError):
            pass
        if self.lag is None:
            self.lag = 0.0
        else:
            try:
                self.lag = float(self.lag)
            except (ValueError, TypeError, AttributeError):
                pass
        try:
            self.complete = float(self.complete)
        except (ValueError, TypeError, AttributeError):
            pass

    def make_key(self, keystr):
        self.key = hashlib.md5(keystr.encode('ascii')).hexdigest()[:6]

    def add_note(self, note):
        self.note.append(note)

    def gen_script_entry(self, entrytype, entryname, projectname):
        kwlist = []
        for par in self.parameters:
            val = getattr(self, par)
            if val is not None:
                if par in gu.DATE_FIELDS:
                    val = gu.datedeltastr(val)
                elif par in gu.LIST_FIELDS:
                    val = '|'.join(val)
                else:
                    val = str(val)
                sp = "'"
                if par == 'duration':  # Because here there is always a begins/ends
                    val = False
                if par in ['status', 'complete']:
                    try:
                        val = float(val)
                        sp = ''
                    except ValueError:
                        pass
                if val:
                    kwlist.append(f"{par}={sp}{val}{sp}")
        s = f"{entryname} = gantt.{entrytype}({', '.join(kwlist)})\n"
        s += f"{projectname}.add_{entrytype.lower()}({entryname})"
        return s


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
        self.parameters = ['name', 'date', 'owner', 'label', 'status', 'note', 'updated', 'complete',
                           'predecessors', 'lag', 'groups', 'colinear', 'marker', 'color']
        if name is None:
            return
        super().__init__(name=name, **kwargs)
        self.type = 'milestone'
        self.date = gu.datetimedelta(date)
        if self.marker is None:
            self.marker = 'D'
        self.make_key(name)
        self.init_timing(kwargs)

    def init_timing(self, kwargs):
        self.predecessor_timing = False
        provided_timing = set()
        for key in ['date', 'predecessors']:
            if key in kwargs and isinstance(getattr(self, key), (datetime.datetime, list)):
                provided_timing.add(key)
        if len(provided_timing) == 2:
            raise ValueError("Can't provide date and predecessors.")
        if provided_timing == {'predecessors'}:
            print("Not doing that yet...(Predecessors)")
            self.predecessor_timing = True  # This flag will be looked for later in project

    def __repr__(self):
        return f"{self.key}:  {self.name}  {self.date} "

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
        try:
            self.parameters = self.tl_parameters + self.parameters
        except AttributeError:
            self.parameters = self.tl_parameters
        if name is None:
            return
        super().__init__(name=name, **kwargs)
        self.type = 'timeline'
        self.make_key(name)
        self.init_timing(kwargs)

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
            print("Not doing that yet...(Predecessors)")
            self.predecessor_timing = True  # This flag will be looked for later in project
        else:
            if 'duration' not in provided_timing:
                self.duration = self.ends - self.begins
            elif 'ends' not in provided_timing:
                self.ends = self.begins + self.duration
            elif 'begins' not in provided_timing:
                self.begins = self.ends - self.duration

    def __repr__(self):
        return f"{self.key}:  {self.name}  {self.begins} -  {self.ends}"

    def get_color(self):
        if self.color is None or self.color == 'auto':
            return gu.color_palette[0]
        return self.color

    def add_note(self, note):
        self.note.append(note)


class Task(Timeline):
    def __init__(self, name, **kwargs):
        self.parameters = ['owner', 'status', 'complete']
        super().__init__(name=name, **kwargs)
        self.type = 'task'

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
        if jot is None:
            return
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
        self.type = 'note'
        self.make_key(jot)

    def add_reference(self, key):
        """
        Key of entry referenced by this note.
        """
        self.reference.append(key)