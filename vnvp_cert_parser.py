# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import logging
from constants import VNVP_CERT_FILE_PATH, CERTIFICATE
from log_parser import LogParser


class CertificateParser(LogParser):

    def __init__(self):
        self.file = None
        self.res = None

    def init(self, root_dir, res, type=None):
        self.res = res
        self.file = os.path.join(root_dir, VNVP_CERT_FILE_PATH)

    def parse(self):
        if not os.path.exists(self.file):
            self.res[VNVP_CERT_FILE_PATH] = False
            return
        self.res[VNVP_CERT_FILE_PATH] = True
        logging.debug("Parsing  {0}".format(self.file))
        with open(self.file) as f:
            self.res[CERTIFICATE] = f.read()

    def summarize(self):
        pass
