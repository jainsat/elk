# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from elasticsearch import Elasticsearch
from constants import MGR, SUPPORT_BUNDLE, UUID, ESX
from datetime import datetime
from utils import Utils
import json
import re
import os
import gzip
import requests
import logging

TIMESTAMP_REGEX = "(?P<timestamp>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.{0,1}[0-9]{0,3}Z).*"

class NoAttributeFoundException(Exception):
    def __init__(self, attr, config):
        self.attr = attr
        self.config = config

    def __str__(self):
        return "'{0}' attribute is not found in {1}".format(self.attr,
                                                            self.config)


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
            self.handle(node_ip, node_type, v)

    def handle(self, node_ip, node_type, node_data):
        config = Utils.get_config(node_type)
        if not config:
            raise Exception("No config found for logs of type {0}".
                            format(node_type))

        root_dir = node_data.get(SUPPORT_BUNDLE)

        with open("elk/configs/{0}".format(config)) as f:
            log_info = json.load(f).get("logs")
            if not log_info:
                raise NoAttributeFoundException("logs", config)
            for info in log_info:
                log_dir = info.get("logDir")
                log_files = info.get("logFiles")

                if log_dir is None:
                    raise NoAttributeFoundException("logDir", config)

                if log_files is None:
                    raise NoAttributeFoundException("logFiles", config)

                log_dir_full_path = os.path.join(root_dir, log_dir)
                log_files = self.find_files(log_dir_full_path,
                                            log_files)

                logging.debug("Processing following log files for type {0}.".
                              format(node_type))
                logging.debug(log_files)

                patterns = None
                custom_parser = None

                if info.get("patternFiles"):
                    patterns = self.extract_patterns(info.get("patternFiles"))

                if info.get("customParser"):
                    custom_parser = Utils.get_class("elk.parsers." +
                                                    info.get("customParser"))()

                if patterns is None and custom_parser is None:
                    raise Exception("No pattern or custom parser provided for" \
                                    "{0}".format(log_dir))

                for file in log_files:
                    if file.endswith(".gz"):
                        f = gzip.open(file)
                        zipped = True
                    else:
                        f = open(file)
                        zipped = False

                    if custom_parser:
                        kvs = custom_parser.pre()
                        if kvs is not None and len(kvs) > 0:
                            self.es.index(index=self.index, body=res)
                    for line in f:
                        if zipped:
                            line = line.decode("utf-8")

                        res = {}

                        # Add some basic info
                        if res is not None:
                            res["ip_address"] = node_ip
                            res["uuid"] = node_data.get(UUID)
                            res["entity"] = node_type
                            res["file"] = file
                            res["line"] = line
                            res["timestamp"] = self.extract_timestamp(line)

                        if patterns:
                            items = self.apply_patterns(line.rstrip(), patterns)
                            if res.get("status"):
                                res["status"] = res["status"].upper()
                            if items:
                                res.update(items)
                                self.es.index(index=self.index, body=res)

                        if custom_parser:
                            if custom_parser.process(line, res):
                                self.es.index(index=self.index, body=res)

                    f.close()
                    if custom_parser:
                        kvs = custom_parser.post()
                        if kvs is not None and len(kvs) > 0:
                            self.es.index(index=self.index, body=res)

                if custom_parser:
                    kvs = custom_parser.finish()
                    if kvs is not None and len(kvs) > 0:
                        self.es.index(index=self.index, body=res)

    def extract_timestamp(self, line):
        m = re.search(TIMESTAMP_REGEX, line)
        if m:
            try:
                ts = datetime.strptime(m.group("timestamp"),
                                       "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                ts = datetime.strptime(m.group("timestamp"),
                                       "%Y-%m-%dT%H:%M:%SZ")
            return ts

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













