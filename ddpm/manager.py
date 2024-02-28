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
        self.ledger.read()  # read data for the ledger
        self.budget_category_accounts = getattr(acl, self.yaml_data['categories'])  # get the account codes for each budget category
        self.ledger.get_budget_categories(self.budget_category_accounts)  # subtotal the ledger into budget categories
        self.ledger.get_budget_aggregates(self.budget.aggregates)  # add the budget category aggregates from sponsor to ledger
        # Pull out the complete set of categories and aggregates
        self.categories = sorted(set(list(self.budget.categories.keys()) + list(self.ledger.budget_categories.keys())))
        self.aggregates = sorted(set(list(self.budget.aggregates.keys()) + list(self.ledger.budget_aggregates.keys())))

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
            categories = copy(self.categories)
            if 'not_included' in categories:
                asumt = 0.0
                for amtt in self.ledger.amount_types:
                    asumt += abs(self.ledger.subtotals['not_included'][amtt])
                if asumt < 1.0:
                    categories.remove('not_included')
        if aggregates is None:
            aggregates = self.aggregates
        if report:
            fig_ddp = 'fig_ddp.png'
            fig_chart = 'fig_chart.png'
        else:
            fig_ddp = False
            fig_chart = False
        self.table_data = []
        print("M119 - ugly dashboard")
        if 'actual' in self.ledger.subtotals[categories[0]]:
            actual = 'actual'
        else:
            actual = list(self.ledger.amount_types.keys())[0]
        self.headers = ['Category', 'Budget'] + [x for x in self.ledger.amount_types]
        for cat in categories:
            bal = self.budget.budget[cat] - self.ledger.subtotals[cat][actual]
            data = [self.budget.budget[cat]] + [self.ledger.subtotals[cat][x] for x in self.ledger.amount_types]
            self.table_data.append([cat] + [ul.print_money(x) for x in data])
        for agg in aggregates:
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


