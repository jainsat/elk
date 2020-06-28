# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import logging
import sys
from constants import ESX, EDGE, KVM_UBU, IP_ADDR, SUPPORT_BUNDLE
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
    def __init__(self, root_dir, uuid_to_data, type):
        self.root_dir = root_dir
        self.type = type
        self.uuid_to_data = uuid_to_data
        logging.debug("root directory = {0}".format(self.root_dir))

    def process(self):
        final_parser_pipeline = parser_pipeline + tn_mapping[self.type]
        res = {}
        res[SUPPORT_BUNDLE] = self.root_dir
        for parser in final_parser_pipeline:
            parser.init(self.root_dir, res, self.type)
            parser.parse()

        if res.get(IP_ADDR):
            key = "{0}#{1}".format(self.type, res.get(IP_ADDR))
            self.uuid_to_data[key] = res

        else:
            print("No IP address found for {0}", self.root_dir)
            sys.exit(1)


