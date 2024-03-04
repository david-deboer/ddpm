#! /usr/bin/env python
import argparse
from ddpm import utils_ledger as utils
from os import path

ap = argparse.ArgumentParser(description="Perform xlsx -> csv actions based on 'file_indicator'.")
ap.add_argument('file_indicator', help="File indicator: <FY> (int), 'summary', <file_name.tag> (str)")
ap.add_argument('-d', '--directory', help="Directory with the xls file", default='~/Downloads')
ap.add_argument('-t', '--file-type', dest='file_type', default='auto',
                choices=['summary', 'detail', 'auto'])
ap.add_argument('--split', help="Set if splitting funds out of a master file.", action='store_true')
args = ap.parse_args()

basedir = path.expanduser(args.directory)

try:
    fy = int(args.file_indicator)
    xlsin = path.join(basedir, "General Ledger Detail.xlsx")
    csvout = f"FY{fy}_General_Ledger_Detail.csv"
except ValueError:
    if args.file_indicator == 'summary':
        xlsin = path.join(basedir, "General Ledger Summary.xlsx")
        csvout = "General_Ledger_Summary.csv"
    else:
        if args.file_indicator.endswith(".xlsx"):
            xlsin = args.file_indicator
            csvout = f"{args.file_indicator.split('.')[0]}.csv"
        elif args.file_indicator.endswith(".csv"):
            xlsin = None
            csvout = args.file_indicator
        else:
            raise ValueError("Need to include a file tag.")

if args.file_type == 'auto':
    if 'detail' in csvout.lower():
        args.file_type = 'detail'
    elif 'summary' in csvout.lower():
        args.file_type = 'summary'
    else:
        raise ValueError("Unknown file type.")

if args.file_type == 'detail':
    args.legend_starts_with = "Accounting Period"
    args.data_ends_with = 'Grand Total'
else:
    args.legend_starts_with = "Dept ID - Desc"
    args.data_ends_with = 'Grand Total'

if xlsin is not None:
    print(f"   >>>Reading {xlsin}")
    utils.xls2csv(xlsin, csvout)
    import os
    os.remove(xlsin)
print(f"   >>>Scrubbing {args.file_type} csv file {csvout}.")
utils.scrub_csv(csvout, args.legend_starts_with, args.data_ends_with)

if args.split:
    print(f"Splitting {csvout}")
    utils.split_csv(csvout)
