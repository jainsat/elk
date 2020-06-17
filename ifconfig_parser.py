# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import re
import logging
from constants import IFCONFIG_PATH, IP_ADDR
from log_parser import LogParser


class IfConfigParser(LogParser):

    def parse(self, manager_root_dir, res):
        ifconfig_file_path = os.path.join(manager_root_dir, IFCONFIG_PATH)
        logging.debug("Parsing  {0}".format(ifconfig_file_path))
        with open(ifconfig_file_path) as f:
            line = f.readline()
            while line:
                if line.find("eth0") == 0:
                    # read next line.
                    line = f.readline()
                    ip_addr = re.search("inet addr:(?P<ip>.*?)? ", line).group(
                        'ip')
                    res[IP_ADDR] = ip_addr
                    break
                line = f.readline()

    def summarize(self, res):
        summary = ""
        if res.get(IP_ADDR):
            summary = "IP Address = {0}\n".format(res[IP_ADDR])
        else:
            summary = "Could not find IP address.\n"
        return summary
