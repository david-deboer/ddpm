date_types = ['date']

# Give a lot of forgiving variants...
def_amt_choice = {'actual': ['actual'],
                  'a': ['actual'],
                  'actual+encumbrance': ['actual', 'encumbrance'],
                  'a+e': ['actual', 'encumbrance'],
                  'budget': ['budget'],
                  'b': ['budget'],
                  'encumbrance': ['encumbrance'],
                  'e': ['encumbrance']
                  }
def amount_choices(sel):
    if isinstance(sel, list):
        return sel
    if isinstance(sel, str):
        return def_amt_choice[sel]

def get_amount_types(report_type):
    amount_types = []
    for data in ledger_info(report_type=report_type)[1].values():
        if data[1] == 'lumoney':
            amount_types.append(data[0])
    return amount_types

def init_entry(report_type, seed_entry=None):
    ledger_entries = []
    for data in ledger_info(report_type=report_type)[1].values():
        ledger_entries.append(data[0])
    this_entry = {}
    for entry in ledger_entries:
        this_entry[entry] = ''
    if seed_entry is not None:
        this_entry.update(seed_entry)
    return this_entry


def ledger_info(report_type='calanswers'):
    if report_type == 'calanswers':
        key = {'col': 'Account - Desc', 'converter': lambda x: x.split('-')[0].strip()}
        colmap = {'Accounting Period - Desc': ['period', lambda x: str(x)],
                  'Dept ID - Desc': ['deptid', lambda x: x.split('-')[0].strip()],
                  'Fund - Desc': ['fund', lambda x: x.split('-')[0].strip()],
                  'CF1 Code': ['cf1', lambda x: x.strip()],
                  'CF2 Code': ['cf2', lambda x: x.strip()],
                  'Program Code': ['program', lambda x: str(x).strip()],
                  'Account - Desc': ['account', lambda x: str(x)],
                  'Journal Date': ['date', 'ludate'],
                  'Document ID': ['docid', lambda x: str(x)],
                  'Description': ['description', lambda x: str(x)],
                  'Detailed Description': ['detailed_description', lambda x: str(x)],
                  'Reference': ['reference', lambda x: str(x)],
                  'Approver Name': ['approver', lambda x: str(x)],
                  'Preparer Name': ['preparer', lambda x: str(x)],
                  'Authorized Budget Amount': ['budget', 'lumoney'],
                  'Encumbrance Amount': ['encumbrance', 'lumoney'],
                  'Actuals Amount': ['actual', 'lumoney']
                  }
    elif report_type == 'fund_summary':
        key = {'col': 1, 'converter': lambda x: int(x.split('-')[0])}
        colmap = {'Dept ID - Desc': ['deptid', lambda x: str(x)],
                  'Fund - Desc': ['fund', lambda x: str(x)],
                  'Account Category': ['account', lambda x: str(x)],
                  'Authorized Budget Amount': ['budget', 'lumoney'],
                  'Actuals Amount': ['actual', 'lumoney'],
                  'Encumbrance Amount': ['encumbrance', 'lumoney'],
                  'Remaining Balance': ['remaining', 'lumoney']
                  }
    return key, colmap

