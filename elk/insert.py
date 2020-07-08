# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from elasticsearch import Elasticsearch
from constants import MGR
from datetime import datetime
import json
import re
import os
import gzip

class ELK:
    def __init__(self, root_dir, ctype):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.root_dir = root_dir
        self.ctype = ctype

    def insert(self):
        if self.ctype == MGR:
            self.handle_ccp()



    def handle_ccp(self):
        with open("ccp.json") as f:
            data = json.load(f).get("logs")
        for d in data:
            log_dir = d.get("logDir")
            log_file_pattern = d.get("logFile")
            grep_pats = d.get("grep")
            print(log_dir)
            print(log_file_pattern)
            print(grep_pats)
            log_root = os.path.join(self.root_dir, log_dir)
            files = os.listdir(log_root)
            print(files)
            matched_files = [os.path.join(log_root, f) for f in files if re.match(log_file_pattern, f)]
            print("Files found for ccp = {0}".format(matched_files))
            for mf in matched_files:
                with gzip.open(mf, 'r') as f:
                    for i, line in enumerate(f):
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
                                ts = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
                                res = {"timestamp": ts, "entity": "ccp", "milestone": label, "status": "PASS", "file": mf }
                                self.es.index(index="test-index", body=res)
                                grep_pats.remove(pat)
                                break

            print(grep_pats)
            for pat in grep_pats:
                label = pat.get("label")
                res = {"timestamp": datetime.utcnow(), "entity": "ccp", "milestone": label,
                       "status": "FAIL"}
                self.es.index(index="test-index", body=res)
                print("yo")





ELK("/Users/satya/Downloads/nsx_unfed/nsx_manager_372739d7-6197-4426-81fb-782a35e7bfa9_20191104_065006", MGR).insert()








