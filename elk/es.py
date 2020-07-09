# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from elasticsearch import Elasticsearch
from constants import MGR, SUPPORT_BUNDLE, UUID, ESX
from datetime import datetime
import json
import re
import os
import gzip
import requests

class ES:
    def __init__(self, ip_to_data, index_name):
        self.host = "localhost"
        self.port = "9200"
        self.es = Elasticsearch(['http://localhost:9200'])
        self.ip_to_data = ip_to_data
        self.index = index_name

    def delete_index(self):
        url = "http://{0}:{1}/{2}".format(self.host, self.port, self.index)
        response = requests.delete(url)
        if response.status_code != 200 and response.status_code != 404:
            print(response.text)

    def insert(self):
        for k,v in self.ip_to_data.items():
            arr = k.split("#")
            node_type = arr[0]
            node_ip = arr[1]
            if node_type == MGR:
                self.handle_ccp(v.get(SUPPORT_BUNDLE), node_ip, v)
            if node_type == ESX:
                self.handle_esx(v.get(SUPPORT_BUNDLE), node_ip, v)

    def handle_ccp(self, root_dir, node_ip, node_data):
        with open("elk/ccp.json") as f:
            data = json.load(f).get("logs")
        for d in data:
            log_dir = d.get("logDir")
            log_file_pattern = d.get("logFile")
            grep_pats = d.get("grep")
            print(log_dir)
            print(log_file_pattern)
            print(grep_pats)
            log_root = os.path.join(root_dir, log_dir)
            files = os.listdir(log_root)
            print(files)
            matched_files = self.find_files(log_root, log_file_pattern)
            print("Files found for ccp = {0}".format(matched_files))
            for mf in matched_files:
                if mf.endswith(".gz"):
                    f = gzip.open(mf)
                    zipped = True
                else:
                    f = open(mf)
                    zipped = False
                for i, line in enumerate(f):
                    if zipped:
                        line = line.decode("utf-8")
                    #print(line)
                    if len(grep_pats) == 0:
                        break
                    for pat in grep_pats:
                        lookup = pat.get("lookup")
                        label = pat.get("label")
                        if line.find(lookup) >= 0:
                            ts = str(line.split()[0].strip())
                            print(ts)
                            try:
                                ts = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
                            except ValueError:
                                ts = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

                            res = {"timestamp": ts,
                                   "entity": "ccp",
                                   "event": label,
                                   "status": "PASS",
                                   "file": mf,
                                   "ip_address": node_ip,
                                   "uuid": node_data.get(UUID)
                                   }
                            self.es.index(index=self.index, body=res)
                            grep_pats.remove(pat)
                            break

            print(grep_pats)
            for pat in grep_pats:
                label = pat.get("label")
                res = {"timestamp": datetime.utcnow(), "entity": "ccp", "milestone": label,
                       "status": "FAIL"}
                self.es.index(index=self.index, body=res)
                print("yo")


    def handle_esx(self, root_dir, node_ip, node_data):
        with open("elk/esx.json") as f:
            log_info = json.load(f).get("logs")
        for info in log_info:
            log_dir = info.get("logDir")
            log_file_patterns = info.get("logFiles")
            log_dir_full_path = os.path.join(root_dir, log_dir)
            log_files = self.find_files(log_dir_full_path, log_file_patterns)
            pattern_files = info.get("patternFiles")
            patterns = self.extract_patterns(pattern_files)
            print(log_files)
            print(patterns)
            for file in log_files:
                if file.endswith(".gz"):
                    f = gzip.open(file)
                    zipped = True
                else:
                    f = open(file)
                    zipped = False
                print("processing " + file)
                for line in f:
                    if zipped:
                        line = line.decode("utf-8")

                    res = self.apply_patterns(line.rstrip(), patterns)
                    if res is not None:
                        res["ip_address"] = node_ip
                        res["uuid"] = node_data.get(UUID)
                        res["entity"] = ESX
                        res["file"] = file
                        try:
                            ts = datetime.strptime(res.get("timestamp"), "%Y-%m-%dT%H:%M:%S.%fZ")
                        except ValueError:
                            ts = datetime.strptime(res.get("timestamp"), "%Y-%m-%dT%H:%M:%SZ")
                        res["timestamp"] = ts
                        self.es.index(index=self.index, body=res)
                f.close()


    def find_files(self, dir, patterns):
        res = []
        all_files = os.listdir(dir)
        for file in all_files:
            for pattern in patterns:
                if re.search(pattern, file):
                    res.append(os.path.join(dir, file))
                    break
        return res

    def extract_patterns(self, pattern_files):
        patterns = []
        for file in pattern_files:
            file = os.path.join("elk/patterns", file)
            with open(file) as f:
                for line in f.readlines():
                    patterns.append(line.rstrip())
        return patterns

    def apply_patterns(self, line, patterns):
        for pattern in patterns:
            m = re.search(pattern, line)
            if m is not None:
                print(m.groupdict())
                return m.groupdict()













