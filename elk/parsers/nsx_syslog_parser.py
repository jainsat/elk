# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from elk.parsers.custom_parser import CustomParser


class NsxSyslogParser(CustomParser):

    def process(self, line, timestamp, parse_all=False):
        res = {}
        if line.find("VersionMastershipHandshakeClient: connection") > 0:
            parts = line.split()
            res['line'] = line
            res['timestamp'] = timestamp
            res["log_level"] = parts[9].split('"')[1]
            res["remote_uuid"] = parts[-3][:-1]
            res["remote_ip"] = parts[-1].split("/")[-1]
            res["event"] = "VersionMastershipHandshakeClient: connection " + parts[-5][:-1]
            return res

        if line.strip().endswith("Start nsx proxy"):
            res['event'] = "Start nsx proxy"
            res['log_level'] = "INFO"
            res['line'] = line
            res['timestamp'] = timestamp
            return res

        if line.find("MasterResponse Calllog_level") > 0:
            parts = line.split()
            res['line'] = line
            res['timestamp'] = timestamp
            res['event'] = "MasterResponse Calllog_level " + parts[14]
            res['log_level'] = parts[9].split('"')[1]
            return res









