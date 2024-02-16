"""
This provides the overall analysis for budget and ledger.  The input yaml defines the parameters

"""

import yaml
from . import account_code_list as acl
from . import ledger
from . import ledger_utils as lu
from . import plot_finance as plot
from tabulate import tabulate


class Finance:
    def __init__(self, yaml_file):
        self.yaml_file = yaml_file
        with open (self.yaml_file, 'r') as fp:
            self.yaml_data = yaml.safe_load(fp)

    def get(self):
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
        # In fill as necessary so ledger/budget have complete categories/aggregates -- I don't think I need this...
        # for cat, agg in zip(self.categories, self.aggregates):
        #     if cat not in self.budget.categories:
        #         self.budget.budget[cat] = 0.0
        #     if agg not in self.budget.aggregates:
        #         self.budget.budget[agg] = 0.0
        #     if cat not in self.ledger.budget_categories:
        #         for amtt in self.ledger.amount_types:
        #             self.ledger.subtotals[cat][amtt] = 0.0
        #     if agg not in self.ledger.budget_aggregates:
        #         for amtt in self.ledger.amount_types:
        #             self.ledger.subtotals[agg][amtt] = 0.0

    def dashboard(self, categories=None, aggregates=None, report=False):
        if categories is None:
            categories = self.categories
        if aggregates is None:
            aggregates = self.aggregates
        table_data = []
        for cat in categories:
            bal = self.budget.budget[cat] - self.ledger.subtotals[cat]['actual']
            data = [self.budget.budget[cat], self.ledger.subtotals[cat]['actual'], bal, self.ledger.subtotals[cat]['budget'], self.ledger.subtotals[cat]['encumbrance']]
            table_data.append([cat] + [lu.print_money(x) for x in data])
        for agg in aggregates:
            bal = self.budget.budget[agg] - self.ledger.subtotals[agg]['actual']
            data = [self.budget.budget[agg], self.ledger.subtotals[agg]['actual'], bal, self.ledger.subtotals[agg]['budget'], self.ledger.subtotals[agg]['encumbrance']]
            table_data.append(['+'+agg] + [lu.print_money(x) for x in data])
        bal = self.budget.grand_total - self.ledger.grand_total['actual']
        data = [self.budget.grand_total, self.ledger.grand_total['actual'], bal, self.ledger.grand_total['budget'], self.ledger.grand_total['encumbrance']]
        table_data.append(['Grand Total'] + [lu.print_money(x) for x in data])
        pcremain = 100.0 * bal / self.budget.grand_total
        pcspent = 100.0 * self.ledger.grand_total['actual'] / self.budget.grand_total
        print(f"Percent spent: {pcspent:.1f}")
        print(f"Percent remainint:  {pcremain:.1f}")

        print()
        print(tabulate(table_data, headers=['Category', 'Budget', 'Actual', 'Balance', 'Ledger Budget', 'Encumbrance'], stralign='right', colalign=('left',)))
        plot.plt.figure('Dashboard')
        bamts = [self.budget.budget[cat] for cat in self.categories]
        plot.chart(self.categories, bamts, label='Budget', width=0.7)
        lamts = [self.ledger.subtotals[cat]['actual'] for cat in self.categories]
        plot.chart(self.categories, lamts, label='Ledger', width=0.4)

        if report:
            print("MAKE TEX REPORT")
            plot.tex_dashboard()