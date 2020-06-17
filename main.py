# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import sys
import logging
from optparse import OptionParser
from ccp_parser import CcpParser

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    parser.add_option("-b", "--bug_id", dest="bug_id",
                      help="Bug id on Bugzilla where the summary should be posted.")
    parser.add_option("-t", "--tn_logs", dest="tn_log_path",
                      help="Path to transport node's support bundle.")
    parser.add_option("-c", "--ccp_logs", dest="ccp_log_path",
                      help="Path to CCP support bundle.")
    parser.add_option("-f", "--federation_logs", dest="federation_log_path",
                      help="Path to  CCP support bundle in Federation use case.")
    parser.add_option("-d", "--dest_dir", dest="dest_dir",
                      help="Directory where support bundle should be extracted.")
    (options, _) = parser.parse_args()
    if options.tn_log_path is None \
            and options.ccp_log_path is None \
            and options.federation_log_path is None:
        print("Please provide the path to at least one support bundle.")
        sys.exit(1)
    if options.dest_dir is None:
        options.dest_dir = os.getcwd()
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)

    logging.debug(options)
    if options.ccp_log_path:
        CcpParser(options.ccp_log_path, options.dest_dir).parse()






