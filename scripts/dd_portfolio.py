#! /usr/bin/env python
from ddpm import manager

pf = manager.Portfolio()
pf.get_portfolio_from_tex()
pf.write_csv()