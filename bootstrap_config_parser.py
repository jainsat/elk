# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import logging
import os
from constants import BOOTSTRAP_CONFIG_PATH, UUID
from log_parser import LogParser


class BootStrapConfigParser(LogParser):

    def parse(self, manager_root_dir, res):
        bootstrap_file_path = os.path.join(manager_root_dir, BOOTSTRAP_CONFIG_PATH)
        logging.debug("Parsing  {0}".format(bootstrap_file_path))
        with open(bootstrap_file_path) as f:
            line = f.readline()
            while line:
                if line.find("node_uuid") > 0:
                    res[UUID] = line.split("\"")[3]
                line = f.readline()

    def summarize(self, res):
        summary = ""
        if res.get(UUID):
            summary = "UUID = {0}\n".format(res[UUID])
        else:
            summary = "UUID not found!!!\n"
        return summary