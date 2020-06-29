# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import constants
from summarizer import Summarizer


class MgrSummarizer(Summarizer):
    def __init__(self, data, key):
        self.data = data
        self.key = key

    def summarize(self):
        arr = self.key.split("#")
        node_type = arr[0]
        val = self.data.get(self.key)

        # basic
        with open("templates/basic") as f:
            print(f.read().format(node_type, val.get(constants.SUPPORT_BUNDLE)))

        # ifconfig
        with open("templates/ifconfig_summary") as f:
            print(f.read().format(val.get(constants.IP_ADDR)))

        # clustering.json
        with open('templates/clustering_json_summary') as f:
            print(f.read().format(val.get(constants.UUID)))

        if node_type == constants.MGR:
            with open("templates/netstat_ccp_summary") as f:
                print(f.read().format(val.get(constants.CCP_LISTENING),
                                      val.get(constants.TN)))