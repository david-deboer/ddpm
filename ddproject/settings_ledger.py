from dateutil.parser import parse


def ledger_info(report_type, columns):
    if report_type == 'calanswers':
        return Calanswers(report_type, columns)
    elif report_type == 'fund_summary':
        return FundSummary(report_type, columns)

class BaseType:
    def __repr__(self):
        s = f"  {self.report_type}: key = {self.key}\n"
        for key, val in self.reverse_map.items():
            s += f"\t{key}: {val}\n"
        return s

    def set_columns(self, value):
        self.columns = value

    def make_amt(self, x):
        """
        Convert accounting formatted money to a float
        """
        if isinstance(x, (int, float)):
            return float(x)
        trial = x.replace("(", "-").replace("'", "").replace("$", "").replace(")", "").replace(",", "")
        try:
            return float(trial)
        except ValueError:
            return 0.0

    def make_date(self, x):
        return parse(x).astimezone()

    def clean(self, x):
        return str(x).strip()

    def cpliti(self, x, c, i):
        return str(x).split(c)[i].strip()

    def init(self, seed_entry=None):
        this_entry = {}
        for entry in self.all:
            this_entry[entry] = ''
        if seed_entry is not None:
            this_entry.update(seed_entry)
        return this_entry

    def _get_all(self):
        self.all = []
        self.reverse_map = {}
        for key, val in self.colmap.items():
            self.all.append(val['name'])
            self.reverse_map[val['name']] = key

    def keygen(self, row):
        return self.cpliti(row[self.key_ind], '-', 0)

class Calanswers(BaseType):
    def __init__(self, report_type, columns):
        self.report_type = report_type
        self.columns = columns
        self.key = 'Account - Desc'
        self.key_ind = self.columns.index(self.key)
        self.date_types = ['date']
        self.amount_types = ['actual', 'budget', 'encumbrance']
        self.colmap = {'Accounting Period - Desc': {'name': 'period', 'func': self.clean},
                       'Dept ID - Desc': {'name': 'deptid', 'func': lambda x: self.cpliti(x, '-', 0)},
                       'Fund - Desc': {'name': 'fund', 'func': lambda x: self.cpliti(x, '-', 0)},
                       'CF1 Code': {'name': 'cf1', 'func': self.clean},
                       'CF2 Code': {'name': 'cf2', 'func': self.clean},
                       'Program Code': {'name': 'program', 'func': self.clean},
                       'Account - Desc': {'name': 'account', 'func': self.clean},
                       'Journal Date': {'name': 'date', 'func': self.make_date},
                       'Document ID': {'name': 'docid', 'func': self.clean},
                       'Description': {'name': 'description', 'func': self.clean},
                       'Detailed Description': {'name': 'detailed_description','func':  self.clean},
                       'Reference': {'name': 'reference', 'func': self.clean},
                       'Approver Name': {'name': 'approver', 'func': self.clean},
                       'Preparer Name': {'name': 'preparer', 'func': self.clean},
                       'Authorized Budget Amount': {'name': 'budget', 'func': self.make_amt},
                       'Encumbrance Amount': {'name': 'encumbrance', 'func': self.make_amt},
                       'Actuals Amount': {'name': 'actual','func':  self.make_amt}
                       }
        self._get_all()


class FundSummary:
    def __init__(self, report_type, columns):
        self.report_type = report_type
        self.columns = columns
        self.key = 'Dept ID - Desc'
        self.key_ind = self.columns.index(self.key)
        self.colmap = {'Dept ID - Desc': {'name': 'deptid', 'func': self.clean},
                       'Fund - Desc': {'name': 'fund','func': self.clean},
                       'Account Category': {'name': 'account', 'func': self.clean},
                       'Authorized Budget Amount': {'name': 'budget', 'func': self.get_amt},
                       'Actuals Amount': {'name': 'actual', 'func': self.get_amt},
                       'Encumbrance Amount': {'name': 'encumbrance', 'func': self.get_amt},
                       'Remaining Balance': {'name': 'remaining', 'func': self.get_amt}
                       }
        self._get_all()
