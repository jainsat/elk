# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import tarfile
import logging
from constants import MGR, EDGE, KVM_UBU, ESX, UNKNOWN, GLOB_MGR, NSX_ISSUE_PATH

class Utils:


    @staticmethod
    def extract(filename, dest_dir):
        if Utils.is_tar_gzipped(filename):
            return Utils.extract_tgz_file(filename, dest_dir)

    @staticmethod
    def get_abs_name(name):
        name = name.rstrip("/")
        arr = name.split("/")
        return arr[-1]


    @staticmethod
    def extract_tgz_file(filename, dest_dir):
        assert Utils.is_tar_gzipped(filename), \
            'Invalid file extension: Expected .tgz or .tar.gz, found {0}'.format(filename)
        logging.debug("Extracting {0}".format(filename))
        tar = tarfile.open(filename, 'r:gz')
        if dest_dir is None:
            dest_dir = os.getcwd()
        tar.extractall(path=dest_dir)
        top_dir = os.path.commonprefix(tar.getnames())
        tar.close()
        return top_dir

    @staticmethod
    def is_tar_gzipped(filename):
        return filename.endswith(".tgz") or filename.endswith(".tar.gz")


    @staticmethod
    def check_nsx_issue(dir_name):
        if os.path.isdir(dir_name):
            nsx_issue_file = os.path.join(dir_name, NSX_ISSUE_PATH)
            if os.path.isfile(nsx_issue_file):
                with open(nsx_issue_file) as f:
                    line = f.readline()
                    while line:
                        if line.find("node-type") == 0:
                            val = line.split(":")[1].strip()
                            if val == GLOB_MGR:
                                return GLOB_MGR
                            elif val.startswith("nsx-manager"):
                                return MGR
                            elif val.find("edge") >= 0:
                                return EDGE
                            elif val.find("esx") >= 0:
                                return ESX
                        line = f.readline()


    @staticmethod
    def get_log_type(name):
        nsx_issue_type = Utils.check_nsx_issue(name)
        if nsx_issue_type:
            return nsx_issue_type
        name = Utils.get_abs_name(name)
        if name.lower().startswith("nsx_manager_"):
            return MGR
        if name.lower().startswith("nsx_global_manager_"):
            return GLOB_MGR
        if name.lower().find("edge") >= 0:
            return EDGE
        if name.lower().find("esx") >= 0:
            return ESX
        if name.lower().find("ubuntukvm") >= 0:
            return KVM_UBU
        return UNKNOWN

