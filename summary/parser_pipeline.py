# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import logging
import sys
from constants import ESX, EDGE, KVM_UBU, IP_ADDR, SUPPORT_BUNDLE, MGR, \
    GLOB_MGR
from summary.controller_info_parser import ControllerInfoParser
from summary.esx_version_parser import EsxVersionParser
from summary.dpkg_parser import DpkgParser
from summary.netstat_parser import NetStatParser
from summary.ifconfig_parser import IfConfigParser
from summary.clustering_json_parser import ClusteringJsonParser
from summary.vnvp_cert_parser import CertificateParser


esx_parser_pipeline = [ControllerInfoParser(), NetStatParser(), EsxVersionParser()]
edge_parser_pipeline = [ControllerInfoParser(), NetStatParser(), DpkgParser()]
kvm_parser_pipeline = [ControllerInfoParser(), NetStatParser(), DpkgParser()]

ccp_parse_pipeline = [IfConfigParser(), ClusteringJsonParser(), NetStatParser(), CertificateParser()]
global_mgr_parser_pipeline = [IfConfigParser(), ClusteringJsonParser()]

type_pipeline_mapping = {ESX: esx_parser_pipeline,
                         EDGE: edge_parser_pipeline,
                         KVM_UBU: kvm_parser_pipeline,
                         MGR: ccp_parse_pipeline,
                         GLOB_MGR: global_mgr_parser_pipeline}


class ParserPipeline:
    def __init__(self, root_dir, ip_to_data, type):
        self.root_dir = root_dir
        self.type = type
        self.ip_to_data = ip_to_data
        logging.debug("root directory = {0}".format(self.root_dir))

    def process(self):
        parser_pipeline = type_pipeline_mapping.get(self.type)
        if parser_pipeline is None:
            raise Exception("No parser pipeline defined for type {0}".format(self.type))
        res = {SUPPORT_BUNDLE: self.root_dir}
        for parser in parser_pipeline:
            parser.init(self.root_dir, res, self.type)
            parser.parse()

        if res.get(IP_ADDR):
            key = "{0}#{1}".format(self.type, res.get(IP_ADDR))
            self.ip_to_data[key] = res

        else:
            print("No IP address found for {0}", self.root_dir)
            sys.exit(1)


