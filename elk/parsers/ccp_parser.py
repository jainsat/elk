# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from elk.parsers.custom_parser import CustomParser
from datetime import datetime, timedelta

# String to look for in log file.
events = [
    "CCP process started",
    "Ending full sync, session and sequence ids are now",
    "Notifying listeners that underlying store full sync is complete",
    "MP and ZK full sync are complete. Join cluster",
    "Cluster is up now",
    "NsxCcpRpcServer started"
]

# Kibana label for this event. This is how the events listed above
# will be shown in Kibana,
labels = [
    "CCP process started",
    "MP-CCP full sync completed",
    "Underlying store full sync complete",
    "MP and ZK full sync complete",
    "Cluster is up",
    "NsxCcpRpcServer started"
]

TOTAL_EVENTS = len(events)


class CcpParser(CustomParser):
    def __init__(self):
        # Event number which is expected next.
        self.expected_event_num = 0

        # Whether CCP process started at least once.
        self.first_event_found = False

        # Timestamp associated with last event captured.
        self.last_event_timestamp = datetime.utcnow()

    def process(self, line, timestamp, parse_all=False):
        """
        All the events are expected to happen one after the other. If one
        event is not found then all the subsequent events won't happen and we'll
        publish FAIL records for all of them.
        """
        record = {'line': line, 'timestamp': timestamp}

        expected_event = events[self.expected_event_num]

        if line.find(expected_event) >= 0:
            if not self.first_event_found:
                self.first_event_found = True
            res = record.copy()
            res['event'] = labels[self.expected_event_num]
            res['log_level'] = "INFO"
            self.last_event_timestamp = res["timestamp"]
            self.expected_event_num = (self.expected_event_num + 1) % TOTAL_EVENTS
            return res

        if line.find("Cluster is down") >= 0:
            res = record.copy()
            res["log_level"] = "WARN"
            res["event"] = "Cluster is down"
            self.expected_event_num = 4
            return res

        # If expected event is not found, then we check if the line matches with
        # other events. Since events happen one after the other, this should
        # be possible only if CCP process restarted (i.e. first event).
        match_found = self.match_against_all_events(line)
        if match_found:
            assert match_found == 0
            return self.build_failure_records(match_found)

        if line.find("registering connection NettyConnection") > 0:
            if line.find("CCP-Site") < 0 and line.find("CCP-") > 0:
                res = record.copy()
                res["log_level"] = "INFO"
                words = line.split()
                res["remote_uuid"] = words[-1][1:-1]
                remote_ip_port = words[-5].split("=")[-1][:-2]
                res["remote_port"] = remote_ip_port.split(":")[1]
                res["remote_ip"] = remote_ip_port.split(":")[0]
                res["event"] = "RPC Register Connection"
                return res

        if line.find("Unregistering accepted NettyConnection") > 0:
            if line.find("CCP-") > 0:
                res = record.copy()
                res["log_level"] = "INFO"
                words = line.split()
                res["event"] = "RPC Unregister Connection"
                remote_ip_port = words[-5].split("=")[-1][:-2]
                res["remote_port"] = remote_ip_port.split(":")[1]
                res["remote_ip"] = remote_ip_port.split(":")[0]
                return res

        if line.find("Open mastership for") > 0:
            if line.find("CCP-") > 0:
                res = record.copy()
                res["log_level"] = "INFO"
                words = line.split()
                res["event"] = "Open Mastership"
                res["remote_uuid"] = words[-5][:-1]
                return res

        if line.find("Close mastership for transport node") > 0:
            res = record.copy()
            res["log_level"] = "INFO"
            words = line.split()
            res["event"] = "Close Mastership"
            res["remote_uuid"] = words[-6][:-1]
            res["controller"] = words[-1][:-1]
            return res

        if line.find("FATAL") >= 0:
            res = record.copy()
            res['log_level'] = "FATAL"
            return res
        elif line.find("ERROR") >= 0:
            res = record.copy()
            res['log_level'] = "ERROR"
            return res
        elif line.find("WARN") >= 0:
            res = record.copy()
            res['log_level'] = "WARN"
            return res
        if parse_all:
            print("here " + str(type(parse_all)))
            return record

    def build_failure_records(self, match_found):
        records = []
        i = self.expected_event_num
        while i != match_found:
            record = {"log_level": "NOT_FOUND", "event": events[i]}
            self.last_event_timestamp += timedelta(seconds=1)
            record["timestamp"] = self.last_event_timestamp
            records.append(record)
            i = (i + 1) % TOTAL_EVENTS

        return records

    def finish(self):
        # If no events were found or event sequence didn't complete.
        if not self.first_event_found or self.expected_event_num > 0:
            return self.build_failure_records

    @staticmethod
    def match_against_all_events(line):
        for i, event in enumerate(events):
            if line.find(event) >= 0:
                return i

