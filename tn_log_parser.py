# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import logging
from utils import Utils
from constants import NODE_TYPE
from controller_info_parser import ControllerInfoParser

parser_pipeline= [ControllerInfoParser()]

class TnParser:
    def __init__(self, support_bundle_path, dest_dir):
        self.res = {}
        # Extract the logs.
        # Some times, the root folder is zipped multiple times.
        self.top_dir = Utils.extract(support_bundle_path, dest_dir)
        while os.path.isfile(os.path.join(dest_dir,self.top_dir)):
            self.top_dir = Utils.extract(support_bundle_path, dest_dir)
        self.top_dir_full_path = os.path.join(dest_dir, self.top_dir)
        logging.debug("root directory = {0}".format(self.top_dir_full_path))


    def process(self):
        self.res[NODE_TYPE] = self.get_node_type()
        with open("templates/basic_tn") as f:
            summary = f.read()
        summary = summary.format(self.res[NODE_TYPE], self.top_dir_full_path)

        for parser in parser_pipeline:
            parser.parse(self.top_dir_full_path, self.res)
            summary = summary + parser.summarize(self.res)

        print(summary)





    def get_node_type(self):
        if self.is_esx_node():
            return "ESX"
        elif self.is_edge_node():
            return "EDGE"
        elif self.is_ubuntu_kvm_node():
            return "Ubuntu KVM"
        elif self.is_rhel_kvm_node():
            return "RHEL KVM"
        else:
            return "Unknown"

    def is_edge_node(self):
        return self.top_dir.startswith("nsx_edge_")

    def is_esx_node(self):
        return self.top_dir.startswith("esx")

    def is_ubuntu_kvm_node(self):
        return self.top_dir.startswith("nsx_ubuntukvm_")

    def is_rhel_kvm_node(self):
        # TODO: Cross check this.
        return self.top_dir.startswith("nsx_rhelkvm_")
