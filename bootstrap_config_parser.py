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
            logging.debug("Found {0}".format(self.file))
        else:
            logging.debug("Could not find {0}.".format(self.file))

        with open('templates/bootstrap_config_summary') as f:
            summary = f.read().format(self.res.get(UUID_CONTROLLER))
        return summary

