# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import logging
from utils import Utils
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
    def __init__(self, support_bundle_path, dest_dir):
        self.res = {}
        # Extract the logs.
        # Some times, the root folder is zipped multiple times.
        self.top_dir = Utils.extract(support_bundle_path, dest_dir)
        if self.top_dir == "":
            # KVM
            dirs = os.listdir(dest_dir)
            for file in dirs:
                if file.startswith("nsx_ubuntu"):
                    self.res[NODE_TYPE] = KVM_UBU
                    self.top_dir = Utils.extract(os.path.join(dest_dir, file), dest_dir)

        self.top_dir_full_path = os.path.join(dest_dir, self.top_dir)
        logging.debug("root directory = {0}".format(self.top_dir_full_path))

    def process(self):
        self.res[NODE_TYPE] = self.get_node_type()
        with open("templates/basic_tn") as f:
            summary = f.read()
        summary = summary.format(self.res[NODE_TYPE], self.top_dir_full_path)

        final_parser_pipeline = parser_pipeline + tn_mapping[self.res[NODE_TYPE]]
        for parser in final_parser_pipeline:
            parser.init(self.top_dir_full_path, self.res, self.res[NODE_TYPE])
            parser.parse()
            logging.debug("done")
            summary = summary + parser.summarize()

        print(summary)

    def get_node_type(self):
        if self.is_esx_node():
            return ESX
        elif self.is_edge_node():
            return EDGE
        else:
            return KVM_UBU

    def is_edge_node(self):
        return self.top_dir.startswith("nsx_edge_")

    def is_esx_node(self):
        return self.top_dir.startswith("esx")

    def is_ubuntu_kvm_node(self):
        return self.top_dir.startswith("nsx_ubuntukvm_")

    def is_rhel_kvm_node(self):
        # TODO: Cross check this.
        return self.top_dir.startswith("nsx_rhelkvm_")
