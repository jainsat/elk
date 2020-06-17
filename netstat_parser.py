# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import logging
from constants import NETSTAT_PATH, CCP_LISTENING


class NetStatParser:

    def parse(self, manager_root_dir, res):
        netstat_file_path = os.path.join(manager_root_dir, NETSTAT_PATH)
        logging.debug("Parsing  {0}".format(netstat_file_path))
        with open(netstat_file_path) as f:
            line = f.readline()
            while line:
                if line.find("0.0.0.0:1235") > 0:
                    arr = line.split()
                    if arr[5] == "LISTEN":
                        res[CCP_LISTENING] = True
                    break
                line = f.readline()

    def summarize(self, res):
        summary = ""
        if res.get(CCP_LISTENING):
            summary = "CCP is listening at port 1235.\n"
        else:
            summary = "CCP is not listening at port 1235!!!\n"
        return summary

