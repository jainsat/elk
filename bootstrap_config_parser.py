# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import logging
import os
from constants import BOOTSTRAP_CONFIG_PATH, UUID_CONTROLLER, BOOTSTRAP_CONFIG_PRESENT
from log_parser import LogParser


class BootStrapConfigParser(LogParser):

    def __init__(self):
        self.file = None
        self.res = None

    def init(self, root_dir, res, type=None):
        self.res = res
        self.file = os.path.join(root_dir, BOOTSTRAP_CONFIG_PATH)

    def parse(self):
        if os.path.exists(self.file):
            self.res[BOOTSTRAP_CONFIG_PRESENT] = True
        else:
            self.res[BOOTSTRAP_CONFIG_PRESENT] = False
            return

        logging.debug("Parsing  {0}".format(self.file))
        with open(self.file) as f:
            line = f.readline()
            while line:
                if line.find("node_uuid") > 0:
                    self.res[UUID_CONTROLLER] = line.split("\"")[3]
                line = f.readline()

    def summarize(self):
        if self.res[BOOTSTRAP_CONFIG_PRESENT]:
            summary = "Found {0}\n".format(self.file)
        else:
            summary = "Could not find {0}.\n".format(self.file)
            return summary

        if self.res.get(UUID_CONTROLLER):
            summary = summary + "UUID = {0}\n\n".format(self.res[UUID_CONTROLLER])
        else:
            summary = summary + "UUID not found!!!\n\n"
        return summary

