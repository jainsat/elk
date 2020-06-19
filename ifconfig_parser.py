# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import re
import logging
from constants import IFCONFIG_PATH, IP_ADDR, IFCONFIG_PRESENT
from log_parser import LogParser


class IfConfigParser(LogParser):

    def __init__(self):
        self.file = None
        self.res = None

    def init(self, root_dir, res, type=None):
        self.res = res
        self.file = os.path.join(root_dir, IFCONFIG_PATH)

    def parse(self):
        if not os.path.exists(self.file):
            self.res[IFCONFIG_PRESENT] = False
            return
        self.res[IFCONFIG_PRESENT] = True
        logging.debug("Parsing  {0}".format(self.file))
        with open(self.file) as f:
            line = f.readline()
            while line:
                if line.find("eth0") == 0:
                    # read next line.
                    line = f.readline()
                    ip_addr = re.search("inet addr:(?P<ip>.*?)? ", line).group(
                        'ip')
                    self.res[IP_ADDR] = ip_addr
                    break
                line = f.readline()

    def summarize(self):
        if self.res[IFCONFIG_PRESENT]:
            summary = "Found {0}\n".format(self.file)
        else:
            return"Could not find {0}.\n".format(self.file)
        if self.res.get(IP_ADDR):
            summary = summary + "IP Address = {0}\n\n".format(self.res[IP_ADDR])
        else:
            summary = summary + "Could not find IP address.\n\n"
        return summary
