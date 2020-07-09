# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import sys
import logging
from optparse import OptionParser
from ccp_parser import CcpParser
from tn_log_parser import TnParser
from utils import Utils
from constants import MGR, EDGE, KVM_UBU, ESX, UNKNOWN, GLOB_MGR
from tn_summarizer import TnSummarizer
from mgr_summarizer import MgrSummarizer
from elk.kibana_utils import KibanaApi
from string import Template
from elk.es import ES
import pprint

ip_to_data = {}


def is_root(dir_name):
    if os.path.exists(os.path.join(dir_name, "etc")):
        return True
    return False


def get_parser(type, root_dir):
    if type == MGR or type == GLOB_MGR:
        return CcpParser(root_dir, ip_to_data, type)
    elif type == ESX or type == EDGE or type == KVM_UBU:
        return TnParser(root_dir, ip_to_data, type)
    else:
        logging.debug("No parser of type {0} found".format(type))
        return UNKNOWN


def handle_dir(dir, dest_dir, type=UNKNOWN):
    new_type = Utils.get_log_type(dir)
    if new_type:
        type = new_type
    if type != UNKNOWN and is_root(dir):
        get_parser(type, dir).process()
    else:
        zipped_files = [os.path.join(dir, f) for f in os.listdir(dir) if
              Utils.is_tar_gzipped(f)]
        if len(zipped_files) > 0:
            for zipped_file in zipped_files:
                handle_zipped_file(zipped_file, dest_dir, type)

        dirs = [os.path.join(dir, f) for f in os.listdir(dir) if
                os.path.isdir(os.path.join(dir, f))]

        for d in dirs:
            handle_dir(d, dest_dir, type)


def handle_zipped_file(name, dest_dir, type=UNKNOWN):
    new_type = Utils.get_log_type(name)
    if new_type:
        type = new_type
    old = os.listdir(dest_dir)
    Utils.extract(name, dest_dir)
    new = os.listdir(dest_dir)
    delta = [f for f in new if f not in old]
    for file in delta:
        if Utils.is_tar_gzipped(file):
            handle_zipped_file(os.path.join(dest_dir, file), dest_dir, type)
        elif os.path.isdir(os.path.join(dest_dir, file)):
            new_dir = os.path.join(dest_dir, file)
            handle_dir(new_dir, new_dir, type)


def get_summary():
    summary = ""
    for k, v in ip_to_data.items():
        arr = k.split("#")
        node_type = arr[0]
        if node_type == MGR or node_type == GLOB_MGR:
            summary += MgrSummarizer(ip_to_data, k).summarize()
        else:
            summary += TnSummarizer(ip_to_data, k).summarize()
    return summary


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    parser.add_option("-d", "--dest_dir", dest="dest_dir",
                      help="Directory where support bundle should be extracted.")
    parser.add_option("-l", "--log", dest="log", help="Path to log")
    parser.add_option("-s", "--space", dest="space", help="Kibana space name")
    parser.add_option("-c", "--clear-old", action="store_true", dest="clear", help="Clear the old data")

    (options, _) = parser.parse_args()

    if options.log is None:
        print("Please provide the path to at least one support bundle.")
        sys.exit(1)

    if options.dest_dir is None:
        options.dest_dir = os.getcwd()
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)

    logging.debug(options)

    if options.log:
        if os.path.isfile(options.log):
            handle_zipped_file(options.log, options.dest_dir)
        elif os.path.isdir(options.log):
            handle_dir(options.log, options.dest_dir)
        else:
            print("Invalid input : {0}. Please provide either a zipped file" \
                  " a directory".format(options.log))
            exit(1)

    pprint.pprint(ip_to_data)

    if options.space:
        kibana_api = KibanaApi()
        es_ins = ES(ip_to_data, "test-index-" + options.space.lower())

        # Delete old space and index related to this space.
        kibana_api.delete_space(options.space)
        es_ins.delete_index()

        # Create fresh space
        kibana_api.create_space(options.space)

        # Create index pattern
        index_id = kibana_api.create_index_pattern("test-index*", options.space)

        # Get summary of the logs
        summary = get_summary()

        # Create a markdown UI for summary.
        summary_id = kibana_api.create_markdown("Summary", summary, options.space)
        logging.debug("summary id = " + summary_id)

        # Insert all the data
        es_ins.insert()

        search_id = kibana_api.create_search("Event", index_id, options.space)
        print("search id = " + search_id)

        # create dashboard and attach above visualizations in it.
        # with open("elk/resources/dashboard.json") as f:
        #     t = Template(f.read())
        #     body = t.substitute(SUMMARY_ID=summary_id)
        #     kibana_api.create_ui(body, "dashboard", options.space)

        kibana_api.add_to_dashboard("visualization", summary_id, 23, options.space)

        kibana_api.add_to_dashboard("search", search_id, 23, options.space)

        kibana_api.create_dashboard(options.space)

        print("You can access Kibana at http://localhost:5601/s/{0}".format(options.space.lower()))












