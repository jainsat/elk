# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from summary.tn_summarizer import TnSummarizer
from summary.mgr_summarizer import MgrSummarizer
from constants import MGR, GLOB_MGR


class BundleSummarizer:
    '''
    Summarizes the complete support bundle.
    It uses other entity specific summarizers to create a summary.
    '''
    def __init__(self, ip_to_data):
        self.ip_to_data = ip_to_data

    def get_summary(self):
        summary = ""
        for k, v in self.ip_to_data.items():
            arr = k.split("#")
            node_type = arr[0]
            if node_type == MGR or node_type == GLOB_MGR:
                summary += MgrSummarizer(self.ip_to_data, k).summarize()
            else:
                summary += TnSummarizer(self.ip_to_data, k).summarize()
        return summary
