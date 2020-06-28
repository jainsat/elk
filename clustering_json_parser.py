# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import logging
import json
from constants import CLUSTER_JSON_PATH, IP_ADDR, UUID_CONTROLLER, MGR
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
            logging.debug("Could not find {0}.".format(self.file))
            return

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

