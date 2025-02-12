#! /usr/bin/env python
import argparse
from ddpm import manager

ap = argparse.ArgumentParser()
ap.add_argument('yaml', help="Name of input yaml file")
ap.add_argument('-f', '--files', help="YAML key to use for file list", default='files')
ap.add_argument('-a', '--accounts', help="List of accounts to use", default=None)
ap.add_argument('-s', '--sort_by', help="Columns to sort by", default='account,date')
ap.add_argument('-c', '--category', help="Category to show, or 'all'", default='all')
ap.add_argument('-r', '--reverse', help="Flag to reverse the sort", action='store_true')
ap.add_argument('-t', '--hide_table', help="Don't show the table", action='store_true')
ap.add_argument('-p', '--hide_plot', help="Don't show the plot", action='store_true')
ap.add_argument('-i', '--intellicull', help="Run ledger intellicull first", action='store_true')
ap.add_argument('-x', '--skip_fund_error', help="Flag to skip erroring on different funds", action='store_true')
ap.add_argument('--amounts', help="Type of amounts to use in audit, None uses from yaml.", default=None)
ap.add_argument('--csv', help="Name of csv file to write", default=False)
ap.add_argument('--col', help="Columns to show or 'all'",
                default='account,date,description,detailed_description,reference,actual,amount,budget,encumbrance')
args = ap.parse_args()

mgr = manager.Manager(args.yaml)
mgr.start_audit(file_list=args.files, raise_fund_error=not args.skip_fund_error)
if args.intellicull:
    mgr.ledger.intellicull()
if args.category != 'all':
    mgr.audit.filter.set(account=mgr.budget_category_accounts[args.category])
elif args.accounts is not None:
    args.accounts = args.accounts.split(',')
    mgr.audit.filter.set(account=args.accounts)
mgr.audit.detail(sort_by=args.sort_by, sort_reverse=args.reverse, cols_to_show=args.col, csv=args.csv)
if not args.hide_table:
    mgr.audit.show_table()
if not args.hide_plot:
    mgr.audit.show_plots(args.amounts)
    manager.plot.plt.show()