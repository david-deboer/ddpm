#! /usr/bin/env python
import argparse
from ddproject import finance

ap = argparse.ArgumentParser()
ap.add_argument('yaml', help="Name of input yaml file")
args = ap.parse_args()

f = finance.Finance(args.yaml)
f.get_finance()
f.get_audit()
f.audit.detail()
finance.plot.plt.show()