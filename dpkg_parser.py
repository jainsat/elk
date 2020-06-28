# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import logging
import os
import sys
from log_parser import LogParser
from constants import DPKG_EDGE_PATH, DPKG_KVM_UBU_PATH, PROXY_VERSION, EDGE, \
    KVM_UBU

file_map = {EDGE: DPKG_EDGE_PATH,
            KVM_UBU: DPKG_KVM_UBU_PATH}


class DpkgParser(LogParser):

    def __init__(self):
        self.file = None
        self.type = None
        self.res = None

    def init(self, root_dir, res, type=None):
        self.res = res
        self.type = type
        file = file_map.get(type)
        if not file:
            print("No netstat file found for type {0}\n".format(type))
            sys.exit(1)
        self.file = os.path.join(root_dir, file)

    def parse(self):
        if not os.path.exists(self.file):
            logging.debug("Could not find {0}, so can't tell NSX Proxy Version" \
            .format(self.file))
            return
        logging.debug("Parsing  {0}".format(self.file))
        with open(self.file) as f:
            line = f.readline()
            while line:
                if line.find("nsx-proxy") >= 0:
                    arr = line.split()
                    self.res[PROXY_VERSION] = arr[2]
                    break
                line = f.readline()

