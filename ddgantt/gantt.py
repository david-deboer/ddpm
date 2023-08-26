import matplotlib.pyplot as plt
from copy import copy
from . import plot_gantt
import datetime


DATE_FIELDS = ['date', 'begins', 'ends']
PAST = datetime.datetime(year=2000, month=1, day=1)
FUTURE = datetime.datetime(year=2040, month=12, day=31)


class _Base:
    base_attr_init = ['name', 'owner', 'status']
    def __init__(self, **kwargs):
        for this_attr in self.base_attr_init:
            try:
                setattr(self, this_attr, kwargs[this_attr])
            except KeyError:
                print(f"Was expecting {this_attr} -- setting to None")
                setattr(self, this_attr, None)


class Milestone(_Base):
    def __init__(self, name, date, owner=None, label=None, status=None, marker='d', color=None):
        super().__init__(name=name, owner=owner, status=status)
        self.date = date
        self.label = label
        self.marker = marker
        self.color = color



class Task(_Base):
    def __init__(self, name, begins, ends, owner=None, label=None, status=None, color=None):
        super().__init__(name=name, owner=owner, status=status)
        self.begins = begins
        self.ends = ends
        self.label = label
        self.color = color
        self.sort_info = {}

class Project:
    _TaskSortInfo = {}
    _MilestoneSortInfo = {'begins': 'date', 'ends': 'date'}
    def __init__(self, name, organization=None):
        self.name = name
        self.organization = organization
        self.milestones = []
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def _sort_tasks(self, sortby):
        self.earliest_task = FUTURE
        self.latest_task = PAST
        self.sorted_tasks = {}
        for this_task in self.tasks:
            key = ''
            for par in sortby:
                if par in self._TaskSortInfo:
                    upar = self._TaskSortInfo[par]
                else:
                    upar = par
                uval = getattr(this_task, upar)
                if upar == 'ends':
                    if uval > self.latest_task:
                        self.latest_task = copy(uval)
                if upar == 'begins':
                    if uval < self.earliest_task:
                        self.earliest_task = copy(uval)
                if upar in DATE_FIELDS:
                    uval = uval.strftime('%Y%m%dT%H%M')
                key += uval + '_'
            key += '_t'
            self.sorted_tasks[key] = this_task

    def add_milestone(self, milestone):
        self.milestones.append(milestone)

    def _sort_milestones(self, sortby):
        self.earliest_milestone = FUTURE
        self.latest_milestone = PAST
        self.sorted_milestones = {}
        for this_milestone in self.milestones:
            key = ''
            for par in sortby:
                if par in self._MilestoneSortInfo:
                    upar = self._MilestoneSortInfo[par]
                else:
                    upar = par
                uval = getattr(this_milestone, upar)
                if upar == 'date':
                    if uval > self.latest_milestone:
                        self.latest_milestone = copy(uval)
                    if uval < self.earliest_milestone:
                        self.earliest_milestone = copy(uval)
                if upar in DATE_FIELDS:
                    uval = uval.strftime('%Y%m%dT%H%M')
                key += uval + '_'
            key += '_m'
            self.sorted_milestones[key] = this_milestone

    def plot(self, sortby=['begins', 'name']):
        """
        Make a gantt chart.

        Parameter
        ---------
        sortby : list
           fields to sort by, must be unique.  sort_info dicts map if needed
        """
        self._sort_tasks(sortby)
        self._sort_milestones(sortby)
        allkeys = sorted(list(self.sorted_milestones.keys()) + list(self.sorted_tasks.keys()))
        dates = []
        labels = []
        plotpars = []
        extrema = [min(self.earliest_milestone, self.earliest_task), max(self.latest_milestone, self.latest_task)]
        for key in allkeys:
            if key.endswith('__m'):
                this_milestone = self.sorted_milestones[key]
                dates.append([this_milestone.date, None])
                labels.append(this_milestone.name)
                plotpars.append(['k', 'D'])
            elif key.endswith('__t'):
                this_task = self.sorted_tasks[key]
                dates.append([this_task.begins, this_task.ends])
                labels.append(this_task.name)
                plotpars.append('b')
        plot_gantt.plotGantt(dates, labels, plotpars, extrema)