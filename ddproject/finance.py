"""
This provides the overall analysis for budget and ledger.  The input yaml defines the parameters

"""

import yaml
from . import account_code_list as acl
from . import ledger, plot_finance
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
        self.ledger.read(self.yaml_data['adjust'])  # read data for the ledger
        self.budget_category_accounts = getattr(acl, self.yaml_data['group_type'])  # get the account codes for each budget category
        self.ledger.get_budget_categories(self.budget_category_accounts)  # subtotal the ledger into budget categories
        self.ledger.get_budget_aggregates(self.budget.aggregates)  # add the budget category aggregates from sponsor to ledger
        # Pull out the complete set of categories and aggregates
        self.categories = sorted(set(list(self.budget.categories.keys()) + list(self.ledger.budget_categories.keys())))
        self.aggregates = sorted(set(list(self.budget.aggregates.keys()) + list(self.ledger.budget_aggregates.keys())))
    
    def overview(self, categories=None):
        print("MAKE CHART / SHOW REMAINING")
        table_data = []
        for cat in self.categories:
            difference = self.budget.budget[cat] - self.ledger.subtotals[cat]['actual']
            table_data.append([cat, self.budget.budget[cat], self.ledger.subtotals[cat]['actual'], difference, self.ledger.subtotals[cat]['budget'], self.ledger.subtotals[cat]['encumbrance']])
        for cat in self.aggregates:
            difference = self.budget.budget[cat] - self.ledger.subtotals[cat]['actual']
            table_data.append(['+'+cat, self.budget.budget[cat], self.ledger.subtotals[cat]['actual'], difference, self.ledger.subtotals[cat]['budget'], self.ledger.subtotals[cat]['encumbrance']])
        print(tabulate(table_data, headers=['Category', 'Budget', 'Actual', 'Difference', 'Ledger Budget', 'Encumbrance']))