# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import sys
import logging
from constants import MGR_NETSTAT_PATH, CCP_LISTENING, MGR, ESX, EDGE, KVM_UBU, \
    KVM_UBU_NETSTAT_PATH, CONNECTED_MGR, CONNECTED_MP, ESX_NETSTAT_PATH, \
    EDGE_NETSTAT_PATH, NETSTAT_PRESENT
from log_parser import LogParser

file_map = {ESX: ESX_NETSTAT_PATH,
            EDGE: EDGE_NETSTAT_PATH,
            KVM_UBU: KVM_UBU_NETSTAT_PATH,
            MGR: MGR_NETSTAT_PATH}

class NetStatParser(LogParser):

    def __init__(self):
        self.file = None
        self.type = None
        self.res = None
    
    def init(self, root_dir, res, type=None):
        self.res = res
        self.type = type
        file = file_map.get(type)
        if not file:
            print("No netstat file found for type {0}\n".format(type))
            sys.exit(1)
        self.file = os.path.join(root_dir, file)

    def parse(self):
        if os.path.exists(self.file):
            self.res[NETSTAT_PRESENT] = True
        else:
            self.res[NETSTAT_PRESENT] = False
            return
        if self.type == MGR:
            self.__parse_mgr_netstat()
        else:
            self.__parse_tn_netstat()

    def summarize(self):
        if self.res[NETSTAT_PRESENT]:
            summary = "Found {0}\n".format(self.file)
        else:
            return "Could not find {0}.\n".format(self.file)
        if self.type == MGR:
            return summary + self.__summarize_mgr()
        else:
            return summary + self.__summarize_tn()

    def __summarize_mgr(self):
        if self.res.get(CCP_LISTENING):
            summary = "CCP is listening at port 1235.\n\n"
        else:
            summary = "CCP is not listening at port 1235!!!\n\n"
        return summary

    def __summarize_tn(self):
        if self.res.get(CONNECTED_MGR):
            summary = "NSX Proxy is connected to CCP.\n"
        else:
            summary = "[WARNING] NSX Proxy is not connected to CCP.\n"
        if self.res.get(CONNECTED_MP) == 3:
            summary += "NSX Proxy is connected to all three MPs.\n\n"

        else:
            summary += "[WARNING] NSX Proxy is not connected to all three MPs.\n\n"
        return summary

    def __parse_mgr_netstat(self):
        logging.debug("Parsing  {0}".format(self.file))
        with open(self.file) as f:
            line = f.readline()
            while line:
                if line.find("0.0.0.0:1235") > 0:
                    arr = line.split()
                    if arr[5] == "LISTEN":
                        self.res[CCP_LISTENING] = True
                    break
                line = f.readline()

    def __parse_tn_netstat(self):
        logging.debug("Parsing  {0}".format(self.file))
        with open(self.file) as f:
            line = f.readline()
            while line:
                if line.find(":1235") > 0:
                    arr = line.split()
                    if arr[5] == "ESTABLISHED":
                        self.res[CONNECTED_MGR] = True

                if line.find(":1234") > 0:
                    arr = line.split()
                    if arr[5] == "ESTABLISHED":
                        self.res[CONNECTED_MP] = self.res.get(CONNECTED_MP, 0) + 1

                line = f.readline()

