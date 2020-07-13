# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from elk.parsers.custom_parser import CustomParser

# Key is the string to look for in the log file
# Kibana label for this event
events = {
    "CCP process started": "CCP process started",
    "Ending full sync, session and sequence ids are now": "MP-CCP full sync completed",
    "Notifying listeners that underlying store full sync is complete": "Underlying store full sync complete",
    "MP and ZK full sync are complete. Join cluster": "MP and ZK full sync complete",
    "Cluster is up now": "Cluster is up",
    "NsxCcpRpcServer started": "NsxCcpRpcServer started"
}


class CcpParser(CustomParser):
    def __init__(self):
        self.events_not_found = events.copy()

    def process(self, line, res):
        for event, label in self.events_not_found.items():
            if line.find(event) >= 0:
                res['event'] = label
                res['status'] = "PASS"
                self.events_not_found.pop(event)
                return True
        return False

    def finish(self):
        res = {}
        for event, label in self.events_not_found.items():
            res['event'] = label
            res['status'] = "FAIL"
        return res


