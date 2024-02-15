allowed_proc_options = {'using_amt': 'a',
                        'override_fund_error': False,
                        'make_plots': True,
                        'make_report': True,
                        'group_type': 'nsf',
                        'groups_to_plot': 'all',
                        'plot_time': True}

ledger_entries_def = ['period', 'deptid', 'fund', 'account', 'date', 'docid',
                      'description', 'detailed_description', 'reference',
                      'approver', 'preparer', 'budget', 'encumbrance', 'actual']

ledger_entries_ext = ['period', 'deptid', 'fund', 'cf1', 'cf2', 'program', 'account', 'date',
                      'docid', 'description', 'detailed_description', 'reference',
                      'approver', 'preparer', 'budget', 'encumbrance', 'actual']


ledger_reduced = ['period', 'account', 'date', 'docid', 'description', 'detailed_description', 'actual']

amount_types = ['budget', 'encumbrance', 'actual']

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

def init_entry(seed_entry=None):
    this_entry = {}
    for entry in ledger_entries_ext:
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


ledger_detail = {'sort_reverse': True,
                 'filter_by_amt': '>=|1.0',
                 'filter_by_date': None,
                 'filter_by_value': None,
                 'exclude_accounts': None,
                 'accounts': None,
                 'set_name': 'all',
                 'use_keys': ledger_entries_ext,
                 'csv': False
                 }
ledger_plot = {'cumul_fig_name': 'CumulativeEntries',
               'daily_fig_name': 'Daily',
               'rate_fig_name': 'Rate',
               'rate_span': 90,
               'rate_smoothing': 2,
               'add_time_legend': True,
               'add_chart_legend': True}
