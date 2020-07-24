# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import constants
from summary.summarizer import Summarizer


class MgrSummarizer(Summarizer):
    def __init__(self, data, key):
        self.data = data
        self.key = key
        self.root_dir = os.getenv("ELK_REPO")

    def summarize(self):
        arr = self.key.split("#")
        node_type = arr[0]
        val = self.data.get(self.key)
        summary = ""
        # basic
        with open(os.path.join(self.root_dir, "summary/templates/basic")) as f:
            summary += f.read().format(node_type, val.get(constants.SUPPORT_BUNDLE))

        # ifconfig
        with open(os.path.join(self.root_dir,
                               "summary/templates/ifconfig_summary")) as f:
            summary += f.read().format(val.get(constants.IP_ADDR))

        # clustering.json
        with open(os.path.join(self.root_dir,
                               'summary/templates/clustering_json_summary')) as f:
            summary += f.read().format(val.get(constants.UUID))

        if node_type == constants.MGR:
            with open(os.path.join(self.root_dir,
                                   "summary/templates/netstat_ccp_summary")) as f:
                summary += f.read().format(val.get(constants.CCP_LISTENING),
                                      val.get(constants.TN))

        # This is for some formatting in markdown UI of kibana.
        summary += " #" + "\n\n"
        return summary

