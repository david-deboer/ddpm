"""
This provides the overall analysis for budget and ledger.  The input yaml defines the parameters

"""

import yaml
from . import account_code_list as acl
from . import utils_ledger as ul
from . import utils_time as ut
from . import plots_ledger as plot
from . import reports_ledger as rl
from . import ddproject, components, ledger
from . import audit
from tabulate import tabulate
from datetime import datetime
from copy import copy


class Finance:
    def __init__(self, yaml_file):
        self.yaml_file = yaml_file
        with open (self.yaml_file, 'r') as fp:
            self.yaml_data = yaml.safe_load(fp)
        self.name = f"{self.yaml_data['name']} - {self.yaml_data['fund']}"

    def get_finance(self):
        # Make the sponsor budget from yaml
        self.budget = ledger.Budget(self.yaml_data['budget'])
        # Setup the ledger
        self.ledger = ledger.Ledger(self.yaml_data['fund'], self.yaml_data['files'])  #start a ledger
        self.ledger.read()  # read data for the ledger
        self.budget_category_accounts = getattr(acl, self.yaml_data['categories'])  # get the account codes for each budget category
        self.ledger.get_budget_categories(self.budget_category_accounts)  # subtotal the ledger into budget categories
        self.ledger.get_budget_aggregates(self.budget.aggregates)  # add the budget category aggregates from sponsor to ledger
        # Pull out the complete set of categories and aggregates
        self.categories = sorted(set(list(self.budget.categories.keys()) + list(self.ledger.budget_categories.keys())))
        self.aggregates = sorted(set(list(self.budget.aggregates.keys()) + list(self.ledger.budget_aggregates.keys())))

    def dashboard(self, categories=None, aggregates=None, report=False):
        if categories is None:
            categories = copy(self.categories)
            if 'not_included' in categories and abs(self.ledger.subtotals['not_included']['actual']) < 1.0:
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
        self.headers = ['Category', 'Budget', 'Actual', 'Balance', 'Ledger Budget', 'Encumbrance']
        for cat in categories:
            bal = self.budget.budget[cat] - self.ledger.subtotals[cat]['actual']
            data = [self.budget.budget[cat], self.ledger.subtotals[cat]['actual'], bal, self.ledger.subtotals[cat]['budget'], self.ledger.subtotals[cat]['encumbrance']]
            self.table_data.append([cat] + [ul.print_money(x) for x in data])
        for agg in aggregates:
            bal = self.budget.budget[agg] - self.ledger.subtotals[agg]['actual']
            data = [self.budget.budget[agg], self.ledger.subtotals[agg]['actual'], bal, self.ledger.subtotals[agg]['budget'], self.ledger.subtotals[agg]['encumbrance']]
            self.table_data.append(['+'+agg] + [ul.print_money(x) for x in data])
        bal = self.budget.grand_total - self.ledger.grand_total['actual']
        data = [self.budget.grand_total, self.ledger.grand_total['actual'], bal, self.ledger.grand_total['budget'], self.ledger.grand_total['encumbrance']]
        self.table_data.append(['Grand Total'] + [ul.print_money(x) for x in data])
        pcremain = 100.0 * bal / self.budget.grand_total
        pcspent = 100.0 * self.ledger.grand_total['actual'] / self.budget.grand_total
        print(f"Percent spent: {pcspent:.1f}")
        print(f"Percent remainint:  {pcremain:.1f}")

        print()
        print(tabulate(self.table_data, headers=self.headers, stralign='right', colalign=('left',)))
        plot.plt.figure('Dashboard')
        bamts = [self.budget.budget[cat] for cat in categories]
        plot.chart(categories, bamts, label='Budget', width=0.7)
        lamts = [self.ledger.subtotals[cat]['actual'] for cat in categories]
        plot.chart(categories, lamts, label='Ledger', width=0.4, savefig=fig_chart)

        self.project = ddproject.Project(self.yaml_data['fund'], organization='RAL')
        duration = ut.months_to_timedelta(self.yaml_data['start'], self.yaml_data['duration'])
        task1 = components.Task(name='Period of Performance', begins=self.yaml_data['start'], duration=duration, status=pcspent, updated=datetime.now())
        print(f"\tStart: {task1.begins}")
        print(f"\tEnds: {task1.ends}")
        self.project.add(task1)
        self.project.chart(weekends=False, months=False, figsize=(6, 2), savefig=fig_ddp)

        if report:
            rl.tex_dashboard(self)

    def get_audit(self):
        self.audit = audit.Audit(self.ledger)
        print("Use <>.audit.filter.set(...) and <>.audit.detail(...)")
        print("Do see a budget category:")
        print("\t<>.audit.filter.set(account=<>.budget_category_accounts['staff'])")
