# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import sys
import logging
from optparse import OptionParser
from ccp_parser import CcpParser
from tn_log_parser import TnParser
from utils import Utils
from constants import MGR, EDGE, KVM_UBU, ESX, UNKNOWN, GLOB_MGR

summary = ""

def get_parser(type, root_dir):
    if type == MGR or type == GLOB_MGR:
        return CcpParser(root_dir, type)
    elif type == ESX or type == EDGE or type == KVM_UBU:
        return TnParser(root_dir, type)
    else:
        logging.debug("No parser of type {0} found".format(type))
        return UNKNOWN


def handle_dir(dir, type=UNKNOWN):
    if type == UNKNOWN:
        type = Utils.get_log_type(dir)
    if type != UNKNOWN:
        get_parser(type, dir).process()
    else:
        zipped_files = [f for f in os.listdir(options.dest_dir) if
              Utils.is_tar_gzipped(f)]
        if len(zipped_files) == 0:
            logging.debug("No zipped files found inside {0}\n".format(dir))
            return
        for zipped_file in zipped_files:
            handle_zipped_file(zipped_file, dir, type)


def handle_zipped_file(name, dest_dir, type=UNKNOWN):
    if type == UNKNOWN:
        type = Utils.get_log_type(name)
    old = os.listdir(dest_dir)
    top_dir = Utils.extract(name, dest_dir)
    if type == UNKNOWN:
        type = Utils.get_log_type(top_dir)
    #print("top dir ={0}".format(top_dir))
    if top_dir != "":
        if type != UNKNOWN:
            get_parser(type, os.path.join(dest_dir, top_dir)).process()
        else:
            dest_dir += "/" + top_dir
            handle_dir(dest_dir, type)
    else:
        new = os.listdir(dest_dir)
        delta = [f for f in new if f not in old and Utils.is_tar_gzipped(f)]
        #print(delta)
        for file in delta:
            handle_zipped_file(os.path.join(dest_dir, file), dest_dir, type)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    parser.add_option("-b", "--bug_id", dest="bug_id",
                      help="Bug id on Bugzilla where the summary should be posted.")
    parser.add_option("-d", "--dest_dir", dest="dest_dir",
                      help="Directory where support bundle should be extracted.")
    parser.add_option("-l", "--log", dest="log", help="Path to log")

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
            handle_dir(options.log)







