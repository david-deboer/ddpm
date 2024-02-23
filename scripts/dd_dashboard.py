#! /usr/bin/env python
import argparse
from ddpm import manager

ap = argparse.ArgumentParser()
ap.add_argument('yaml', help="Name of input yaml file")
ap.add_argument('-r', '--report', help="Flag to write report.", action='store_true')
args = ap.parse_args()

mgr = manager.Manager(args.yaml)
mgr.dashboard(report=args.report)
manager.plot.plt.show()

