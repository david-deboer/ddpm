#! /usr/bin/env python
import argparse
from ddproject import finance

ap = argparse.ArgumentParser()
ap.add_argument('yaml', help="Name of input yaml file")
args = ap.parse_args()

fin = finance.Finance(args.yaml)
fin.get()
fin.dashboard()
finance.plot.plt.show()

