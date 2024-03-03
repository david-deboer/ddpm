"""
This provides the overall analysis for budget and ledger.  The input yaml defines the parameters

"""
import yaml
from . import utils_ledger as ul
from . import utils_time as ut
from . import plots_ledger as plot
from . import project, components, ledger, account_code_list, reports_ledger, audit
from tabulate import tabulate
from datetime import datetime
from dateutil.parser import parse


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
        self.ledger = None

    def get_finance(self, file_list):
        """
        Parameter
        ---------
        file_list : str, list
            key to use from the Yaml file for budget is str, else list of filenames

        """
        # Make the sponsor budget from yaml and get account codes
        self.budget = ledger.Budget(data=self.yaml_data)
        self.budget_category_accounts = getattr(account_code_list, self.yaml_data['categories'])  # get the account codes for each budget category
        self._check_and_set_categories()

        # Setup the ledger
        if file_list is None:
            return
        use_files = file_list if isinstance(file_list, list) else self.yaml_data[file_list]
        self.ledger = ledger.Ledger(self.yaml_data['fund'], use_files)  #start a ledger
        self.ledger.read(invert=self.invert)  # read data for the ledger
        self.ledger.get_budget_categories(self.budget.categories)  # subtotal the ledger into budget categories
        self.ledger.get_budget_aggregates(self.budget.aggregates)  # add the budget category aggregates from sponsor to ledger
        print(f"Ledger dates: {self.ledger.first_date.strftime('%Y-%m-%d')} - {self.ledger.last_date.strftime('%Y-%m-%d')}")
        self.budget.categories['not_included'] = self.ledger.budget_categories['not_included']  # Copy over after setting ledger categories

    def _check_and_set_categories(self):
        """
        Check that all self.budget.categories are in account_code_list.

        Note that all budget categories in budget.categories _must_ be in the account_code_list, but not vice versa.
        Aggregates aren't checked here, since they will error out when reading the budget yaml

        """
        # Check and error if an included account is not in the account_code_list.py
        for category in self.budget.categories:
            if category not in self.budget_category_accounts:
                raise ValueError(f"The category {category} from the budget yaml is not in account_code_list.py -- please add.")

        # Check and add if the opposite...
        for category in self.budget_category_accounts:
            if category not in self.budget.categories:
                print(f"The category '{category}' in account_code_list.py is not in the budget for '{self.yaml_data['categories']}' -- adding with budget of 0")
                self.budget.budget[category] = 0.0
            self.budget.categories[category] = self.budget_category_accounts[category]

        # Include a "not_included" category
        self.budget.categories['not_included'] = []  # Will get set after setting the ledger categories in set_finance
        self.budget.budget['not_included'] = 0.0


    def get_schedule(self, status=None):
        """
        Parameter
        ---------
        status : float, None

        """
        now = datetime.now().astimezone()
        self.project = project.Project(self.yaml_data['fund'], organization='RAL')
        if 'end' in self.yaml_data:
            task1 = components.Task(name='Period of Performance', begins=self.yaml_data['start'], ends=self.yaml_data['end'], status=status, updated=now)
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
        if self.ledger is not None:
            ledger_earliest = components.Milestone(name='Earliest ledger entry.', date=self.ledger.first_date, updated=now)
            self.project.add(ledger_earliest, attrname='ledger_earliest')
            ledger_latest = components.Milestone(name='Latest ledger entry.', date=self.ledger.last_date, updated=now)
            self.project.add(ledger_latest, attrname='ledger_latest')

    def _can_skip(self, cat, amt2use):
        if abs(self.budget.budget[cat]) < 1.0 and abs(self.ledger.subtotals[cat][amt2use]) < 1.0:
            if cat != 'not_included':
                print(f"Skipping {cat}-{amt2use} since no budget or expenditure")
            return True
        return False

    def dashboard(self, categories=None, aggregates=None, report=False, amount2use=['actual', 'amount']):
        """
        Parameters
        ----------
        categories : str or None
            Categories to use, None uses all
        aggregates : str o None
            Aggregates to use, None uses all
        report : bool
            Write the pdf report
        amount2use : list
            List of types that should be used to show results -- uses first found that matches report type

        """
        self.get_finance('files')
        if categories is None:
            categories = list(self.budget.categories.keys())
        elif not isinstance(categories, list):
            categories = []
        if aggregates is None:
            aggregates = list(self.budget.aggregates.keys())
        elif not isinstance(aggregates, list):
            aggregates = []

        if report:
            fig_ddp = 'fig_ddp.png'
            fig_chart = 'fig_chart.png'
        else:
            fig_ddp = False
            fig_chart = False

        # Get the amount type you will use
        for amt2use in self.ledger.amount_types:
            if amt2use in amount2use:
                break

        # Make table
        self.table_data = []
        self.headers = ['Category', 'Budget'] + [x for x in self.ledger.amount_types]
        skipped = []
        for cat in categories:
            if self._can_skip(cat, amt2use):
                skipped.append(cat)
                continue
            bal = self.budget.budget[cat] - self.ledger.subtotals[cat][amt2use]
            data = [self.budget.budget[cat]] + [self.ledger.subtotals[cat][x] for x in self.ledger.amount_types]
            self.table_data.append([cat] + [ul.print_money(x) for x in data])
        for agg in aggregates:
            if self._can_skip(agg, amt2use):
                skipped.append(agg)
                continue
            bal = self.budget.budget[agg] - self.ledger.subtotals[agg][amt2use]
            data = [self.budget.budget[agg]] + [self.ledger.subtotals[agg][x] for x in self.ledger.amount_types]
            self.table_data.append(['+'+agg] + [ul.print_money(x) for x in data])
        bal = self.budget.grand_total - self.ledger.grand_total[amt2use]
        data = [self.budget.grand_total] + [self.ledger.grand_total[x] for x in self.ledger.amount_types]
        self.table_data.append(['Grand Total'] + [ul.print_money(x) for x in data])
        try:
            pcremain = 100.0 * bal / self.budget.grand_total
            pcspent = 100.0 * self.ledger.grand_total[amt2use] / self.budget.grand_total
        except ZeroDivisionError:
            pcremain = 0.0
            pcspent = 0.0
        print(f"Percent spent: {pcspent:.1f}")
        print(f"Percent remaining:  {pcremain:.1f}")
        print()
        print(tabulate(self.table_data, headers=self.headers, stralign='right', colalign=('left',)))
        # Remove skipped ones
        for skca in skipped:
            if skca in categories:
                categories.remove(skca)
            if skca in aggregates:
                aggregates.remove(skca)

        # Make plot
        if len(categories):
            plot.plt.figure('Budget Category Dashboard')
            bamts = [self.budget.budget[cat] for cat in categories]
            plot.chart(categories, bamts, label='Budget', width=0.7)
            lamts = [self.ledger.subtotals[cat][amt2use] for cat in categories]
            plot.chart(categories, lamts, label='Ledger', width=0.4)
            plot.plt.legend()
            plot.plt.grid()
            if fig_chart:
                plot.plt.savefig(fig_chart)
        if len(aggregates):
            plot.plt.figure('Budget Aggregate Dashboard')
            bamts = [self.budget.budget[agg] for agg in aggregates]
            plot.chart(aggregates, bamts, label='Budget', width=0.7)
            lamts = [self.ledger.subtotals[agg][amt2use] for agg in aggregates]
            plot.chart(aggregates, lamts, label='Ledger', width=0.4)
            plot.plt.legend()
            plot.plt.grid()

        self.get_schedule(status=pcspent)
        print(f"\tStart: {self.project.task1.begins}")
        print(f"\tEnds: {self.project.task1.ends}")
        self.project.chart(chart='all', sortby=['date'], weekends=False, months=False, figsize=(6, 2), savefig=fig_ddp)

        if report:
            reports_ledger.tex_dashboard(self)

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


