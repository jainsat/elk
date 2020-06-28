# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import logging
import os
from log_parser import LogParser
from constants import ESX_VERSION_FILE_PATH, PROXY_VERSION, ESX_VER_FILE_PRESENT


class EsxVersionParser(LogParser):
    def __init__(self):
        self.file = None
        self.res = None

    def init(self, root_dir, res, type=None):
        self.res = res
        self.file = os.path.join(root_dir, ESX_VERSION_FILE_PATH)

    def parse(self):
        if not os.path.exists(self.file):
            self.res[ESX_VER_FILE_PRESENT] = False
            return
        self.res[ESX_VER_FILE_PRESENT] = True
        logging.debug("Parsing  {0}".format(self.file))
        with open(self.file) as f:
            line = f.readline()
            while line:
                if line.find("nsx-proxy") >= 0:
                    arr = line.split()
                    self.res[PROXY_VERSION] = arr[1]
                    break
                line = f.readline()

    def summarize(self):
        if not self.res[ESX_VER_FILE_PRESENT]:
            logging.debug("Could not {0}, so can't find NSX proxy version" \
                          .format(self.file))

        with open("templates/proxy_version") as f:
            summary = f.read().format(self.res.get(PROXY_VERSION))

        return summary
