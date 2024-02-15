"""
This provides the overall analysis for budget and ledger.  The input yaml defines the parameters

"""

import yaml
from . import account_code_list as acl
from . import ledger


class Finance:
    def __init__(self, yaml_file):
        self.yaml_file = yaml_file
        self.yaml_data = yaml.safe_load(self.yaml_file)