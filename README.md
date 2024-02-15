DD Project has three project domains:  schedule, ledger, budget

A root level yaml file contains the overall summary (data + file references)

1 - schedule

DD Project tracks various components in time, generally to produce a Gantt chart.  A project (ddproject.py) is a set of components.

The components (in components.py) are all based off an Entry baseclass.  The components are:

- Milestone
- Timeline
- Task: a Timeline with an owner, status and complete
- Note

The component parameters are defined in the component itself (i.e. not in Entry, which has to know them.)

2 - ledger

The ledger is the outgrowth of readChartStrings.  Data are contained in a number of csv files with a header and rows of data
The data need to provide for at least: date, description, account code, amount (one of budget, encumbrance, actual)

3 - budget

The budget is part of the outgrowth of readChartStrings.  Currently, the high-level budget is contained with the yaml file, but maybe allow for having a budget csv doc...