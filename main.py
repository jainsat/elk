#!/usr/local/bin/python3
# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import sys
import logging
from optparse import OptionParser
from summary.parser_pipeline import ParserPipeline
from utils import Utils
from constants import UNKNOWN
from elk.kibana_handler import KibanaHandler
from elk.es_handler import EsHandler
from visualize import Visualize
import pprint

ip_to_data = {}


def is_root(dir_name):
    if os.path.exists(os.path.join(dir_name, "etc")):
        return True
    return False


def handle_dir(dir, dest_dir, type=UNKNOWN):
    new_type = Utils.get_log_type(dir)
    if new_type:
        type = new_type
    if type != UNKNOWN and is_root(dir):
        return ParserPipeline(dir, ip_to_data, type).process()
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


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    parser.add_option("-d", "--dest_dir", dest="dest_dir",
                      help="Directory where support bundle should be extracted.")
    parser.add_option("-l", "--log", dest="log", help="Path to log")
    parser.add_option("-b", "--bug_id", dest="space", help="Bug id")
    parser.add_option("-c", "--clear-old", action="store_true", dest="clear",
                      help="Clear the old data present in this space.")
    parser.add_option("-n", "--host", dest="host",
                      help="ELK hostname or ip address", default="10.172.219.243")
    parser.add_option("-k", "--kibana_port", dest="kibana_port",
                      help="Kibana port", default="5601")
    parser.add_option("-e", "--es_port", dest="es_port",
                      help="Elasticsearch port", default="9200")

    parser.add_option("-x", "--export_dashboard_name", dest="ex_dash_name",
                      help="Name of the dashboard to be exported.")

    parser.add_option("-s", "--export_dashboard_space", dest="ex_dash_space",
                      help="Name of the space, where the dashboard to be exported"
                           "exist.")
    parser.add_option("-a", "--parse_all", action="store_true", dest="parse_all",
                      help="Parse all the lines of the log files",
                      default=False)

    (options, _) = parser.parse_args()

    if options.log is None:
        print("Please provide the path to at least one support bundle.")
        sys.exit(1)

    if options.ex_dash_name and options.ex_dash_space is None:
        raise Exception("Please provide space of the dashboard to be exported.")

    if options.dest_dir is None:
        options.dest_dir = os.getcwd()
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)

    logging.debug(options)
    if options.space:
        # Get instance of Kibana Handler.
        kibana_handler = KibanaHandler(options.host, options.kibana_port)

        # Get instance of ElasticSearch Handler.
        es_handler = EsHandler(options.host, options.es_port, "test-index-" +
                           options.space.lower())

        if options.clear:
            # Delete old space and index related to this space.
            kibana_handler.delete_space(options.space.lower())
            es_handler.delete_index()

        # Create fresh space
        created = kibana_handler.create_space(options.space)
        if not created:
            print("Kibana space for this bug id already exist. "
                  "It can be accessed at http://{0}:{1}/s/{2}".
                  format(options.host, options.kibana_port, options.space.lower()))
            print("If you want to re-run everything, then please run the "
                  "script with --clear-old option. Or else give a different "
                  "bug id.")
            exit(0)

        # Create index pattern
        index_id = kibana_handler.create_index_pattern("test-index-" +
                                                   options.space.lower() +
                                                   "*", options.space)

        if options.log:
            if os.path.isfile(options.log):
                handle_zipped_file(options.log, options.dest_dir)
            elif os.path.isdir(options.log):
                handle_dir(options.log, options.dest_dir)
            else:
                print("Invalid input : {0}. Please provide either a zipped file"
                      " a directory".format(options.log))
                exit(1)

        # pprint.pprint(ip_to_data)

        # Insert all the data
        es_handler.insert(ip_to_data, options.parse_all)

        #Create all the visualizations.
        Visualize(es_handler, kibana_handler, options.space,
                  index_id, ip_to_data).visualize(options.ex_dash_name,
                                                  options.ex_dash_space)

        print("You can access Kibana at http://{0}:{1}/s/{2}/app/kibana".
              format(options.host, options.kibana_port, options.space.lower()))

    else:
        print ("No bug id provided. Exiting.")
        exit(0)
