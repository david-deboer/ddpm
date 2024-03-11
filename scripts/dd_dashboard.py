#! /usr/bin/env python
import argparse
from ddpm import manager

ap = argparse.ArgumentParser()
ap.add_argument('yaml', help="Name of input yaml file")
ap.add_argument('-R', '--report', help="Flag to write report.", action='store_true')
ap.add_argument('-r', '--rate', help="Rate of expenditure /day", default=None)
ap.add_argument('-s', '--style', help="Name of style for Gantt", default='default')
ap.add_argument('-b', '--banner', help="Color of banner, if to include", default=None)
args = ap.parse_args()

mgr = manager.Manager(args.yaml)
mgr.dashboard(report=args.report, rate=args.rate, style=args.style, banner=args.banner)
manager.plot.plt.show()

