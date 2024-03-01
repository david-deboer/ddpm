"""
This provides the overall analysis for budget and ledger.  The input yaml defines the parameters

"""
import yaml
from . import account_code_list as acl
from . import utils_ledger as ul
from . import utils_time as ut
from . import plots_ledger as plot
from . import reports_ledger as rl
from . import project, components, ledger
from . import audit
from tabulate import tabulate
from datetime import datetime
from dateutil.parser import parse
from copy import copy


class Manager:
    def __init__(self, yaml_file):
        """
        Parameter
        ---------
        yaml_file : str
            Name of Yaml file
        Attributes
        ----------
        same as above
        name : str
        """
        self.yaml_file = yaml_file
        with open (self.yaml_file, 'r') as fp:
            self.yaml_data = yaml.safe_load(fp)
        self.name = f"{self.yaml_data['name']} - {self.yaml_data['fund']}"
        if 'invert' in self.yaml_data:
            self.invert = self.yaml_data['invert']
        else:
            self.invert = False

    def get_finance(self, file_list):
        """
        Parameter
        ---------
        file_list : str, list
            key to use from the Yaml file for budget is str, else list of filenames

        """
        # Make the sponsor budget from yaml
        self.budget = ledger.Budget(data=self.yaml_data)
        # Setup the ledger
        if file_list is None:
            return
        use_files = file_list if isinstance(file_list, list) else self.yaml_data[file_list]
        self.ledger = ledger.Ledger(self.yaml_data['fund'], use_files)  #start a ledger
        self.ledger.read(invert=self.invert)  # read data for the ledger
        self.budget_category_accounts = getattr(acl, self.yaml_data['categories'])  # get the account codes for each budget category
        self._check_categories_aggregates(self.budget, self.budget_category_accounts)
        self.ledger.get_budget_categories(self.budget.categories)  # subtotal the ledger into budget categories
        self.ledger.get_budget_aggregates(self.budget.aggregates)  # add the budget category aggregates from sponsor to ledger

    def _check_categories(self, budget, cat_from_acl):
        """
        Check that all self.budget.categories are in account_code_list.

        Note that all budget categories in budget.categories _must_ be in the account_code_list, but not vice versa.
        Aggregates aren't checked here, since they will error out when reading the budget yaml

        """
        # Do the checking here
        # Make this, the two lines below and the get_budget_X above consistent
        for category in self.budget.categories:
            if category not in cat_from_acl:
                raise ValueError(f"The category {category} from the budget yaml is not in account_code_list.py -- please add.")
        if 'not_included' not in cat_from_acl:
            cat_from_acl['not_included'] = []
        for category in cat_from_acl:
            if category not in self.budget.categories:
                print(f"The category {category} in account_code_list.py is not in the budget -- adding with budget of 0")
                self.budget.categories[category] = category
                self.budget.budget[category] = 0.0

    def get_schedule(self, status=None):
        """
        Parameter
        ---------
        status : float, None

        """
        now = datetime.now().astimezone()
        self.project = project.Project(self.yaml_data['fund'], organization='RAL')
        if 'end' in self.yaml_data:
            task1 = components.Task(name='Period of Performance', begins=self.yaml_data['start'], ends=self.yaml_data['stop'], status=status, updated=now)
        elif 'duration' in self.yaml_data:
            duration = ut.months_to_timedelta(self.yaml_data['start'], self.yaml_data['duration'])
            task1 = components.Task(name='Period of Performance', begins=self.yaml_data['start'], duration=duration, status=status, updated=now)
        self.project.add(task1, attrname='task1')
        if 'schedule' in self.yaml_data:
            if 'milestone' in self.yaml_data['schedule']:
                ctr = 1
                for mdate, mstatement in self.yaml_data['schedule']['milestone'].items():
                    ms = components.Milestone(name=mstatement, date=mdate, updated=now)
                    self.project.add(ms, attrname=f"ms{ctr}")
                    ctr += 1
            if 'task' in self.yaml_data['schedule']:
                ctr = 1
                for mdate, mstatement in self.yaml_data['schedule']['task'].items():
                    mstart, mstop = [parse(x) for x in mdate.split('_')]
                    tk = components.Task(name=mstatement, begins=mstart, ends=mstop, updated=now)
                    self.project.add(tk, attrname=f"task{ctr}")
                    ctr += 1

    def _can_skip(self, cat, actual):
        if abs(self.budget.budget[cat]) < 1.0 and abs(self.ledger.subtotals[cat][actual]) < 1.0:
            print(f"Skipping {cat}-{actual} since no budget or expenditure")
            return True
        return False

    def dashboard(self, categories=None, aggregates=None, report=False):
        """
        Parameters
        ----------
        categories : str or None
            Categories to use, None uses all
        aggregates : str o None
            Aggregates to use, None uses all
        report : bool
            Write the pdf report

        """
        self.get_finance('files')
        if categories is None:
            categories = list(self.budget.categories.keys())
        if aggregates is None:
            aggregates = list(self.budget.aggregates.keys())
        if report:
            fig_ddp = 'fig_ddp.png'
            fig_chart = 'fig_chart.png'
        else:
            fig_ddp = False
            fig_chart = False
        self.table_data = []
        print("M119 - ugly dashboard actual 'logic'")
        if 'actual' in self.ledger.subtotals[categories[0]]:
            actual = 'actual'
        else:
            actual = list(self.ledger.amount_types.keys())[0]
        self.headers = ['Category', 'Budget'] + [x for x in self.ledger.amount_types]
        for cat in categories:
            if self._can_skip(cat, actual):
                continue
            bal = self.budget.budget[cat] - self.ledger.subtotals[cat][actual]
            data = [self.budget.budget[cat]] + [self.ledger.subtotals[cat][x] for x in self.ledger.amount_types]
            self.table_data.append([cat] + [ul.print_money(x) for x in data])
        for agg in aggregates:
            if self._can_skip(agg, actual):
                continue
            bal = self.budget.budget[agg] - self.ledger.subtotals[agg][actual]
            data = [self.budget.budget[agg]] + [self.ledger.subtotals[agg][x] for x in self.ledger.amount_types]
            self.table_data.append(['+'+agg] + [ul.print_money(x) for x in data])
        bal = self.budget.grand_total - self.ledger.grand_total[actual]
        data = [self.budget.grand_total] + [self.ledger.grand_total[x] for x in self.ledger.amount_types]
        self.table_data.append(['Grand Total'] + [ul.print_money(x) for x in data])
        try:
            pcremain = 100.0 * bal / self.budget.grand_total
            pcspent = 100.0 * self.ledger.grand_total[actual] / self.budget.grand_total
        except ZeroDivisionError:
            pcremain = 0.0
            pcspent = 0.0
        print(f"Percent spent: {pcspent:.1f}")
        print(f"Percent remainint:  {pcremain:.1f}")

        print()
        print(tabulate(self.table_data, headers=self.headers, stralign='right', colalign=('left',)))
        plot.plt.figure('Dashboard')
        print("M182: Include aggregates")
        bamts = [self.budget.budget[cat] for cat in categories]
        plot.chart(categories, bamts, label='Budget', width=0.7)
        lamts = [self.ledger.subtotals[cat][actual] for cat in categories]
        plot.chart(categories, lamts, label='Ledger', width=0.4, savefig=fig_chart)

        self.get_schedule(status=pcspent)
        print(f"\tStart: {self.project.task1.begins}")
        print(f"\tEnds: {self.project.task1.ends}")
        self.project.chart(chart='all', sortby=['date'], weekends=False, months=False, figsize=(6, 2), savefig=fig_ddp)

        if report:
            rl.tex_dashboard(self)

    def show_files(self):
        ul.show_ledger_files(self.ledger)

    def start_audit(self, file_list='files'):
        """
        Parameters
        ----------
        file_list : str
            key to use for list of files to use
        amount_types : list
            list of amount_types to use in the audit

        """
        self.get_finance(file_list=file_list)
        self.audit = audit.Audit(self.ledger)


