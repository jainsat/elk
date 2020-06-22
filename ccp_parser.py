# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import sys
import logging
from utils import Utils
from ifconfig_parser import IfConfigParser
from netstat_parser import NetStatParser
from bootstrap_config_parser import BootStrapConfigParser
from clustering_json_parser import ClusteringJsonParser
from constants import MGR, GLOB_MGR, NSX_ISSUE_PATH

parse_pipeline = [IfConfigParser(), ClusteringJsonParser(), NetStatParser() ]

class CcpParser:
    def __init__(self, root_dir, type=MGR):
        self.root_dir = root_dir
        self.type = type
        if self.type == MGR and self.is_global_manager():
            self.type = GLOB_MGR

    def is_global_manager(self):
        nsx_issue_file = os.path.join(self.root_dir, NSX_ISSUE_PATH)
        if not os.path.exists(nsx_issue_file):
            return False
        with open(nsx_issue_file) as f:
            line = f.readline()
            while line:
                if line.find("node-type") == 0:
                    mgr_type = line.split(":")[1].strip()
                    if mgr_type == GLOB_MGR:
                        return True
                    else:
                        return False
                line = f.readline()
        return False

    def process(self):
        res = {}
        summary = ""
        logging.debug("Processing {0}".format(self.root_dir))
        with open("templates/basic") as f:
            summary = f.read()
        summary = summary.format(self.type, self.root_dir)
        for parser in parse_pipeline:
            parser.init(self.root_dir, res, self.type)
            parser.parse()

            summary = summary + parser.summarize()

        print(summary)
























