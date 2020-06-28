# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import logging
import json
from constants import CLUSTER_JSON_PATH, IP_ADDR, CLUSTER_JSON_PRESENT, \
    UUID_CONTROLLER, GLOB_MGR, MGR
from log_parser import LogParser


class ClusteringJsonParser(LogParser):

    def __init__(self):
        self.file = None
        self.res = None

    def init(self, root_dir, res, type=None):
        self.res = res
        self.type = type
        self.file = os.path.join(root_dir, CLUSTER_JSON_PATH)

    def parse(self):
        if not os.path.exists(self.file):
            self.res[CLUSTER_JSON_PRESENT] = False
            return
        self.res[CLUSTER_JSON_PRESENT] = True
        logging.debug("Parsing  {0}".format(self.file))
        if self.type == MGR:
            manager_key = "CONTROLLER"
        else:
            manager_key = "GLOBAL_MANAGER"
        with open(self.file) as f:
            data = json.load(f)
            for node in data.get('/api/v1/cluster-manager/config').get('nodes'):
                for entity in node.get('entities'):
                    if entity.get('entity_type').strip() == manager_key and \
                            entity.get("ip_address").strip() == self.res[IP_ADDR]:
                        self.res[UUID_CONTROLLER] = entity.get("entity_uuid")
                        return

    def summarize(self):
        if self.res[CLUSTER_JSON_PRESENT]:
            logging.debug("Found {0}".format(self.file))
        else:
            logging.debug("Could not find {0}.".format(self.file))

        with open('templates/clustering_json_summary') as f:
            summary = f.read().format(self.res.get(UUID_CONTROLLER))
        return summary
