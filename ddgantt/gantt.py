import matplotlib.pyplot as plt
from copy import copy
import datetime


DATE_FIELDS = ['date', 'begins', 'ends']


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
        self.sorted_tasks = {}
        for this_task in self.tasks:
            key = ''
            for par in sortby:
                if par in self._TaskSortInfo:
                    upar = self._TaskSortInfo[par]
                else:
                    upar = par
                uval = getattr(this_task, upar)
                if upar in DATE_FIELDS:
                    uval = uval.strftime('%Y%m%dT%H%M')
                key += uval
            self.sorted_tasks[key] = this_task

    def add_milestone(self, milestone):
        self.milestones.append(milestone)

    def _sort_milestones(self, sortby):
        self.sorted_milestones = {}
        for this_milestone in self.milestones:
            key = ''
            for par in sortby:
                if par in self._MilestoneSortInfo:
                    upar = self._MilestoneSortInfo[par]
                else:
                    upar = par
                uval = getattr(this_milestone, upar)
                if upar in DATE_FIELDS:
                    uval = uval.strftime('%Y%m%dT%H%M')
                key += uval
            self.sorted_tasks[key] = this_milestone

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