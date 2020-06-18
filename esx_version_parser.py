# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import logging
import os
from log_parser import LogParser
from constants import ESX_VERSION_FILE_PATH, PROXY_VERSION, ESX_VER_FILE_PRESENT


class EsxVersionParser(LogParser):
    def __init__(self):
        self.__version_file_path = None

    def parse(self, manager_root_dir, res, type=None):
        self.__version_file_path = os.path.join(manager_root_dir, ESX_VERSION_FILE_PATH)
        if not os.path.exists(self.__version_file_path):
            res[ESX_VER_FILE_PRESENT] = False
            return
        res[ESX_VER_FILE_PRESENT] = True
        logging.debug("Parsing  {0}".format(self.__version_file_path))
        with open(self.__version_file_path) as f:
            line = f.readline()
            while line:
                if line.find("nsx-proxy") >= 0:
                    arr = line.split()
                    res[PROXY_VERSION] = arr[1]
                    break
                line = f.readline()

    def summarize(self, res):
        if not res[ESX_VER_FILE_PRESENT]:
            return "{0} does not exist, so can't find NSX proxy version\n" \
                .format(self.__version_file_path)

        with open("templates/proxy_version") as f:
            summary = f.read().format(self.__version_file_path, res[PROXY_VERSION])

        return summary