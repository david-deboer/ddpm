#! /usr/bin/env python

from ddpm import icalendar
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('-f', '--file', help='Name of ics file', default='Hard Constraints.ics')
ap.add_argument('-u', '--upcoming', help='Number of days to include in upcoming', default=30)
ap.add_argument('--eras', help='Eras to plot', default='future,upcoming,next,current')
ap.add_argument('--eras_text', help="Eras for text output", default='current,next,upcoming,future')
ap.add_argument('-a', '--add', help="Add item for purposes of plot/plan - start,stop,summary", default=None)
ap.add_argument('-n', '--no-text', dest='no_text', help="Flag to not show text on plot.", action='store_true')
args = ap.parse_args()

if args.eras == 'all':
    args.eras = ['future', 'upcoming', 'next', 'current', 'past']
else:
    args.eras = args.eras.split(',')
if args.eras_text == 'all':
    args.eras_text = ['past', 'current', 'next', 'upcoming', 'future']
else:
    args.eras_text = args.eras_text.split(',')

if args.add is not None:
    start = args.add.split(',')[0]
    end = args.add.split(',')[1]
    summary = args.add.split(',')[2]

ical = icalendar.iCal(icsfn=args.file)
ical.read_ics(upcoming=args.upcoming)
if args.add is not None:
    ical.add(start=start, end=end, summary=summary)
ical.ical_plot(eras=args.eras,  no_text=args.no_text)
ical.ical_text(eras=args.eras_text)
icalendar.plt.show()