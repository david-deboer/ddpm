"""
This provides the overall analysis for budget and ledger.  The input yaml defines the parameters

"""
import yaml
from . import utils_ledger as ul
from . import utils_time as ut
from . import plots_ledger as plot
from . import project, components, ledger, account_code_list, reports_ledger, audit
from tabulate import tabulate
from datetime import datetime, timedelta
from dateutil.parser import parse


class Manager:
    def __init__(self, yaml_file):
        """
        This sets up the manager by processing the input yaml file data.

        Parameter
        ---------
        yaml_file : str
            Name of Yaml file

        Attributes
        ----------
        yaml_file : str
            Same as Parameter
        yaml_data : dict
            Contents of the input yaml
        name : str
            Generated name of project
        invert : str
            Flag to invert values in ledger
        chart_amounts : list or None
            If list, use those amount_types in plots etc
        ledger, budget, project : None
            Sets up a None version of the ledger, budget and project schedule

        """
        self.yaml_file = yaml_file
        with open (self.yaml_file, 'r') as fp:
            self.yaml_data = yaml.safe_load(fp)
        self.name = f"{self.yaml_data['name']} - {self.yaml_data['fund']}"
        self.invert = self.yaml_data['invert'] if 'invert' in self.yaml_data else False
        self.chart_amounts = ul.get_amount_list(self.yaml_data['chart_amounts']) if 'chart_amounts' in self.yaml_data else None
        self.ledger = None
        self.budget = None
        self.project = None

    def get_finance(self, file_list):
        """
        Read in the ledger and the budget and transfer budget categories to ledger.

        Parameter
        ---------
        file_list : str, list
            key to use from the Yaml file for budget is str, else list of filenames

        Attributes
        ----------
        budget : Budget instance
        budget_category_accounts : dict
        ledger : Ledger instance


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
        self.budget.categories['not_included'] = self.ledger.budget_categories['not_included']  # Copy over after setting ledger categories
        self.budget_category_accounts['not_included'] = self.ledger.budget_categories['not_included']  # Copy over after setting ledger categories (again)

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
        Read any schedule info in yaml and start a project.

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
            ledger_earliest = components.Milestone(name='Earliest ledger entry', date=self.ledger.first_date, updated=now)
            self.project.add(ledger_earliest, attrname='ledger_earliest')
            ledger_latest = components.Milestone(name='Latest ledger entry', date=self.ledger.last_date, updated=now)
            self.project.add(ledger_latest, attrname='ledger_latest')

    def _can_skip(self, cat, amounts):
        if abs(self.budget.budget[cat]) < 1.0 and abs(self.ledger.totaling(cat, amounts)) < 1.0:
            if cat != 'not_included':
                print(f"Skipping {cat}-{'+'.join(amounts)} since no budget or expenditure")
            return True
        return False

    def _make_dash_fig(self, figname, use, amounts, save_it=False):
        if len(use):
            plot.plt.figure(figname)
            bamts = [self.budget.budget[ca] for ca in use]
            plot.chart(use, bamts, label='Budget', width=0.7)
            lamts = [self.ledger.totaling(ca, amounts) for ca in use]
            plot.chart(use, lamts, label='Ledger', width=0.4)
            plot.plt.legend()
            plot.plt.grid()
            if save_it:
                plot.plt.savefig(save_it)

    def dashboard(self, categories=None, aggregates=None, report=False, amounts=None, rate=None, style='default', banner=None):
        """
        Parameters
        ----------
        categories : str or None
            Categories to use, None uses all
        aggregates : str o None
            Aggregates to use, None uses all
        report : bool
            Write the pdf report
        amounts : list
            List of types that should be used to show results -- IF NOT None OVERRIDES self.chart_amounts
        rate : None or float
            Using dd_audit, you can get an estimate of the rate of expenditure/day for the same amounts, if present gives a spend-out date
        style : str
            Name of style for Gantt chart (see styles_proj.py)
            
        """
        self.get_finance('files')
        if categories is None or categories == 'all':
            categories = list(self.budget.categories.keys())
        elif not isinstance(categories, list):
            categories = []
        if aggregates is None or aggregates == 'all':
            aggregates = list(self.budget.aggregates.keys())
        elif not isinstance(aggregates, list):
            aggregates = []
        fig_ledger, fig_chart = ('fig_ledger.png', 'fig_chart.png') if report else (False, False)

        # Get the amount types you will use
        amounts = ul.get_amount_list(amounts=amounts, amount_types=self.ledger.amount_types, chart_amounts=self.chart_amounts)

        # Make table
        self.table_data = []
        self.headers = ['Category', 'Budget', 'Balance'] + [x for x in self.ledger.amount_types]
        use = {}
        for catype, catagg in zip(['cat', 'agg'], [categories, aggregates]):
            use[catype] = []
            for ca in catagg:
                if not self._can_skip(ca, amounts):
                    use[catype].append(ca)
                    bal = self.budget.budget[ca] - self.ledger.totaling(ca, amounts)
                    data = [self.budget.budget[ca], bal] + [self.ledger.subtotals[ca][x] for x in self.ledger.amount_types]
                    self.table_data.append([ca] + [ul.print_money(x) for x in data])
        grand_bal = self.budget.grand_total - self.ledger.totaling('grand', amounts)
        data = [self.budget.grand_total, grand_bal] + [self.ledger.grand_total[x] for x in self.ledger.amount_types]
        self.table_data.append(['Grand Total'] + [ul.print_money(x) for x in data])
        pcremain, pcspent = -999.0, -999.0
        try:
            pcremain = 100.0 * grand_bal / self.budget.grand_total
            pcspent = 100.0 * self.ledger.totaling('grand', amounts) / self.budget.grand_total
        except (ZeroDivisionError, KeyError):
            pass
        print(f"Percent spent: {pcspent:.0f}")
        print(f"Percent remaining:  {pcremain:.0f}\n")
        print(tabulate(self.table_data, headers=self.headers, stralign='right', colalign=('left',)), '\n')

        # Make ledger plots
        self._make_dash_fig('Budget Category Dashboard', use['cat'], amounts, save_it=fig_ledger)
        self._make_dash_fig('Budget Aggregate Dashboard', use['agg'], amounts, save_it=False)

        # Make project
        self.get_schedule(status=pcspent)
        self.sgrand, self.sdept = '', ''
        if rate is None:
            print("Do you want to include a rate/day (-r) for a spend out time (use dd_audit.py)?")
        else:
            now = datetime.now().astimezone()
            rate = float(rate)
            spend_out_grand = components.Milestone(name='Spend out grand total', date=now+timedelta(days = grand_bal / rate), updated=now)
            self.project.add(spend_out_grand, attrname="spend_out_grand")
            self.sgrand = (f"With a grand total balance of {ul.print_money(grand_bal)} at a rate of {ul.print_money(rate)} /day, "
                           f"you will spend out in {grand_bal/rate:.1f} days or by {spend_out_grand.date.strftime('%Y-%m-%d')}")
            if 'department_total' in use['agg']:
                dept_bal = self.budget.budget['department_total'] - self.ledger.totaling('department_total', amounts)
                spend_out_dept = components.Milestone(name='Spend out dept total', date=now+timedelta(days = dept_bal / rate), updated=now)
                self.project.add(spend_out_dept, attrname="spend_out_dept")
                self.sdept = (f"With a dept total balance of {ul.print_money(dept_bal)} at a rate of {ul.print_money(rate)} /day, "
                              f"you will spend out in {dept_bal/rate:.1f} days or by {spend_out_dept.date.strftime('%Y-%m-%d')}")

        print(f"\tStart: {self.project.task1.begins}")
        print(f"\tEnds: {self.project.task1.ends}")
        self.project.chart(chart='all', sortby=['date'], weekends=False, months=False, figsize=(6, 2), savefig=fig_chart, style=style, banner=banner)
        if len(self.sgrand): print(self.sgrand)
        if len(self.sdept): print(self.sdept)
        if report: reports_ledger.tex_dashboard(self)

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
        self.audit = audit.Audit(self.ledger, chart_amounts=self.chart_amounts)


