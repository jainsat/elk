# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import sys
import logging
from utils import Utils
from ifconfig_parser import IfConfigParser
from netstat_parser import NetStatParser
from bootstrap_config_parser import BootStrapConfigParser

parse_pipeline = [IfConfigParser(), BootStrapConfigParser(), NetStatParser() ]

class CcpParser:
    def __init__(self, support_bundle_path, dest_dir):
        self.dest_dir = dest_dir
        self.manager_dirs = []
        if Utils.is_tar_gzipped(support_bundle_path):
            Utils.extract_tgz_file(support_bundle_path, dest_dir)

        # There should be three tgz files in the bundle.
        # and they should have format like nsx_manager_*.tgz.
        dir_content = os.listdir(dest_dir)
        nsx_mgr_files = [item for item in dir_content if \
                         Utils.is_nsx_manager_support_bundle(item)]
        if len(nsx_mgr_files) == 0:
            print("No NSX Manager support bundles found in {0}".format(dest_dir))
            sys.exit(1)

        for f in nsx_mgr_files:
            file_full_path = os.path.join(dest_dir, f)
            top_dir = Utils.extract_tgz_file(file_full_path, dest_dir)
            self.manager_dirs.append(os.path.join(dest_dir, top_dir))


    def parse(self):
        res = {}
        summary = ""
        for i, root_dir in enumerate(self.manager_dirs):
            logging.debug("Processing {0}".format(root_dir))
            summary = summary + "CCP #{0}\n".format(i)
            summary = summary + "Support Bundle = {0}\n".format(root_dir)
            for parser in parse_pipeline:
                parser.parse(root_dir, res)
                summary = summary + parser.summarize(res)

        print("**************** Summary ********************")
        print(summary)
























