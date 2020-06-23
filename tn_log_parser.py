# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import logging
from constants import NODE_TYPE, ESX, EDGE, KVM_UBU
from controller_info_parser import ControllerInfoParser
from esx_version_parser import EsxVersionParser
from dpkg_parser import DpkgParser
from netstat_parser import NetStatParser

parser_pipeline = [ControllerInfoParser(), NetStatParser()]
esx_parser_pipeline = [EsxVersionParser()]
edge_parser_pipeline = [DpkgParser()]
kvm_parser_pipeline = [DpkgParser()]

tn_mapping = {ESX: esx_parser_pipeline,
              EDGE: edge_parser_pipeline,
              KVM_UBU: kvm_parser_pipeline }


class TnParser:
    def __init__(self, root_dir, type):
        self.res = {}
        self.root_dir = root_dir
        self.type = type
        logging.debug("root directory = {0}".format(self.root_dir))

    def process(self):
        with open("templates/basic") as f:
            summary = f.read()

        summary = summary.format(self.type, self.root_dir)

        final_parser_pipeline = parser_pipeline + tn_mapping[self.type]
        for parser in final_parser_pipeline:
            parser.init(self.root_dir, self.res, self.type)
            parser.parse()
            logging.debug("done")
            summary = summary + parser.summarize()

        print(summary)
        print("#" * 75)
        print("\n")


