# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import logging
import sys
from ifconfig_parser import IfConfigParser
from netstat_parser import NetStatParser
from clustering_json_parser import ClusteringJsonParser
from constants import MGR, IP_ADDR, SUPPORT_BUNDLE
from vnvp_cert_parser import CertificateParser

ccp_parse_pipeline = [IfConfigParser(), ClusteringJsonParser(), NetStatParser(), CertificateParser()]
global_mgr_parser_pipeline = [IfConfigParser(), ClusteringJsonParser()]


class CcpParser:
    def __init__(self, root_dir, uuid_to_data, type=MGR):
        self.root_dir = root_dir
        self.type = type
        self.uuid_to_data = uuid_to_data


    def process(self):
        res = {}
        res[SUPPORT_BUNDLE] = self.root_dir
        logging.debug("Processing {0}".format(self.root_dir))

        if self.type == MGR:
            parser_pipeline = ccp_parse_pipeline
        else:
            parser_pipeline = global_mgr_parser_pipeline
        for parser in parser_pipeline:
            parser.init(self.root_dir, res, self.type)
            parser.parse()

        if res.get(IP_ADDR):
            key = "{0}#{1}".format(self.type, res.get(IP_ADDR))
            self.uuid_to_data[key] = res

        else:
            print("No IP address found for {0}", self.root_dir)
            sys.exit(1)























