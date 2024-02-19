#! /usr/bin/env python
import argparse
from ddproject import finance

ap = argparse.ArgumentParser()
ap.add_argument('yaml', help="Name of input yaml file")
ap.add_argument('-r', '--report', help="Flag to write report.", action='store_true')
args = ap.parse_args()

fin = finance.Finance(args.yaml)
fin.get_finance()
fin.dashboard(report=args.report)
finance.plot.plt.show()

