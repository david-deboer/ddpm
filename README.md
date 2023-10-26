DD Project

DD Project tracks various components in time, generally to produce a Gantt chart.  A project (ddproject.py) is a set of components.

The components (in components.py) are all based off an Entry baseclass.  The components are:

- Milestone
- Timeline
- Task: a Timeline with an owner, status and complete
- Note

The component parameters are defined in the component itself (i.e. not in Entry, which has to know them.)