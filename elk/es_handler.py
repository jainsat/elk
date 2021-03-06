# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from constants import MGR, SUPPORT_BUNDLE, UUID, ESX
from datetime import datetime, timezone
from string import Template
import json
import re
import os
import gzip
import requests
import logging


TIMESTAMP_REGEX = "(?P<timestamp>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:" \
                  "[0-9]{2}.{0,1}[0-9]{0,3}Z).*"

BULK_SIZE = 10000

'''
Type to config mapping. Value represents the file name present in config
directory. Key should be one of the types present in constant.py
'''
CONFIG_MAP = {
    MGR: "ccp.json",
    ESX: "esx.json"
}


class NoAttributeFoundException(Exception):
    def __init__(self, attr, config):
        self.attr = attr
        self.config = config

    def __str__(self):
        return "'{0}' attribute is not found in {1}".format(self.attr,
                                                            self.config)


class EsHandler:
    def __init__(self, host, port, index_name):
        self.host = host
        self.port = port
        self.es = Elasticsearch(['http://{0}:{1}'.format(self.host, self.port)])
        self.index = index_name
        self.doc_cache = []
        self.root_dir = os.getenv("ELK_REPO")
        if self.root_dir is None:
            raise Exception("Please set the env variable ELK_REPO")

    def delete_index(self):
        url = "http://{0}:{1}/{2}".format(self.host, self.port, self.index)
        response = requests.delete(url)
        # 404 - if index does not exist.
        if response.status_code != 200 and response.status_code != 404:
            raise Exception(response.text)

    def insert(self, ip_to_data, parse_all=False):
        for k, v in ip_to_data.items():
            arr = k.split("#")
            node_type = arr[0]
            node_ip = arr[1]
            self.handle(node_ip, node_type, v, parse_all)
        self.flush()

    def flush(self):
        if len(self.doc_cache) > 0:
            print("Flushing {0} records".format(len(self.doc_cache)))
            helpers.bulk(self.es, self.doc_cache)
            self.doc_cache.clear()

    def handle_custom_parser_result(self, res, node_type, node_uuid, node_ip,
                                    file=None):
        if res is not None and type(res) is dict:
            self.add_basic_fields(node_ip, node_uuid, node_type, res)
            if file:
                res["file"] = file
                res["_index"] = self.index
            # self.es.index(index=self.index, body=res)
            self.doc_cache.append(res)
        elif res is not None and len(res) > 0:
            for record in res:
                record["_index"] = self.index
                if file:
                    record["file"] = file
                self.add_basic_fields(node_ip, node_uuid, node_type, record)
            self.doc_cache.extend(res)
        if len(self.doc_cache) >= BULK_SIZE:
            self.flush()

    def handle(self, node_ip, node_type, node_data, parse_all=False):
        config = self.get_config(node_type)
        if not config:
            raise Exception("No config found for logs of type {0}".
                            format(node_type))

        root_dir = node_data.get(SUPPORT_BUNDLE)
        node_uuid = node_data.get(UUID)
        with open(os.path.join(self.root_dir, "elk/configs/{0}").format(config)) as f:
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
                    custom_parser = self.get_class("elk.parsers." +
                                                    info.get("customParser"))()

                if patterns is None and custom_parser is None:
                    raise Exception("No pattern or custom parser provided for \
                                    {0}".format(log_dir))

                for file in log_files:
                    if file.endswith(".gz"):
                        f = gzip.open(file)
                        zipped = True
                    else:
                        f = open(file)
                        zipped = False

                    if custom_parser:
                        kvs = custom_parser.pre()
                        self.handle_custom_parser_result(kvs, node_type,
                                                         node_uuid, node_ip,
                                                         file)
                    for line in f:
                        if zipped:
                            line = line.decode("utf-8")

                        if patterns:
                            items = self.apply_patterns(line.rstrip(), patterns)
                            if items:
                                items["line"] = line
                                items["timestamp"] = self.extract_timestamp(line)
                                self.handle_custom_parser_result(items, node_type,
                                                                 node_uuid,
                                                                 node_ip,
                                                                 file)

                        if custom_parser:
                            kvs = custom_parser.process(line,
                                                        self.extract_timestamp(line),
                                                        parse_all)
                            self.handle_custom_parser_result(kvs, node_type,
                                                             node_uuid, node_ip,
                                                             file)

                    f.close()
                    if custom_parser:
                        kvs = custom_parser.post()
                        self.handle_custom_parser_result(kvs, node_type,
                                                         node_uuid, node_ip,
                                                         file)

                if custom_parser:
                    kvs = custom_parser.finish()
                    self.handle_custom_parser_result(kvs, node_type,
                                                     node_uuid, node_ip)


    @staticmethod
    def add_basic_fields(ip, uuid, node_type, res):
        res["ip_address"] = ip
        res["uuid"] = uuid
        res["entity"] = node_type

    @staticmethod
    def get_class(kls):
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m

    @staticmethod
    def get_config(node_tye):
        return CONFIG_MAP.get(node_tye)

    @staticmethod
    def extract_timestamp(line):
        m = re.search(TIMESTAMP_REGEX, line)
        if m:
            try:
                ts = datetime.strptime(m.group("timestamp"),
                                       "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                ts = datetime.strptime(m.group("timestamp"),
                                       "%Y-%m-%dT%H:%M:%SZ")
            return ts.replace(tzinfo=timezone.utc)
        else:
            return datetime.utcnow()

    @staticmethod
    def find_files(dir, patterns):
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
            file = os.path.join(self.root_dir + "/elk/patterns", file)
            with open(file) as f:
                for line in f.readlines():
                    patterns.append(line.rstrip())
        return patterns

    @staticmethod
    def apply_patterns(line, patterns):
        for pattern in patterns:
            m = re.search(pattern, line)
            if m is not None:
                return m.groupdict()

    def query(self, query, cols=None):
        with open(os.path.join(self.root_dir, "elk/resources/es_query.json")) as q:
            query_json = Template(q.read())
            if cols is None:
                payload = query_json.substitute(COLUMNS="*", QUERY=query)
            else:
                payload = query_json.substitute(COLUMNS=",".join(cols), QUERY=query)
        url = "http://{0}:{1}/{2}/_search".format(self.host, self.port,
                                                  self.index)
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("hits").get("hits")
        else:
            logging.debug(response.json())
