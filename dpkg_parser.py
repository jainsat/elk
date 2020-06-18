# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import logging
import os
from log_parser import LogParser
from constants import DPKG_EDGE_PATH, DPKG_KVM_UBU_PATH, PROXY_VERSION, \
    DPKG_PRESENT, EDGE, KVM_UBU


class DpkgParser(LogParser):
    def __init__(self):
        self.__dpkg_file_path = None

    def parse(self, manager_root_dir, res, type=None):
        if type == EDGE:
            self.__dpkg_file_path = os.path.join(manager_root_dir, DPKG_EDGE_PATH)
        else:
            self.__dpkg_file_path = os.path.join(manager_root_dir, DPKG_KVM_UBU_PATH)

        if not os.path.exists(self.__dpkg_file_path):
            res[DPKG_PRESENT] = False
            return
        res[DPKG_PRESENT] = True
        logging.debug("Parsing  {0}".format(self.__dpkg_file_path))
        with open(self.__dpkg_file_path) as f:
            line = f.readline()
            while line:
                if line.find("nsx-proxy") >= 0:
                    arr = line.split()
                    res[PROXY_VERSION] = arr[2]
                    break
                line = f.readline()

    def summarize(self, res):
        if not res[DPKG_PRESENT]:
            return "dpkg file {0} does not exist, so can't tell NSX Proxy Version\n" \
            .format(self.__dpkg_file_path)

        with open("templates/proxy_version") as f:
            summary = f.read().format(self.__dpkg_file_path, res[PROXY_VERSION])

        return summary

