# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import sys
import logging
from constants import MGR_NETSTAT_PATH, CCP_LISTENING, MGR, ESX, EDGE, KVM_UBU, \
    KVM_UBU_NETSTAT_PATH, CONNECTED_MGR, CONNECTED_MP, ESX_NETSTAT_PATH, \
    EDGE_NETSTAT_PATH, NETSTAT_PRESENT, GLOB_MGR, IP_ADDR, TN
from log_parser import LogParser

file_map = {ESX: ESX_NETSTAT_PATH,
            EDGE: EDGE_NETSTAT_PATH,
            KVM_UBU: KVM_UBU_NETSTAT_PATH,
            MGR: MGR_NETSTAT_PATH,
            GLOB_MGR: MGR_NETSTAT_PATH}

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
        if self.type == MGR or self.type == GLOB_MGR:
            self.__parse_mgr_netstat()
        else:
            self.__parse_tn_netstat()

    def summarize(self):
        if self.res[NETSTAT_PRESENT]:
            summary = "Found {0}\n".format(self.file)
        else:
            return "Could not find {0}.\n".format(self.file)
        if self.type == MGR or self.type == GLOB_MGR:
            return summary + self.__summarize_mgr()
        else:
            return summary + self.__summarize_tn()

    def __summarize_mgr(self):
        if self.res.get(CCP_LISTENING):
            summary = "CCP is listening at port 1235.\n"
        else:
            summary = "CCP is not listening at port 1235!!!\n"
        if not self.res.get(TN):
            summary += "No transport nodes are connected to CCP.\n"
        else:
            summary += "Transport nodes connected to CCP: {0}\n".format(self.res[TN])
        summary += "\n"
        return summary

    def __summarize_tn(self):
        if self.res[IP_ADDR]:
            summary = "IP = {0}\n".format(self.res[IP_ADDR])

        if self.res.get(CONNECTED_MGR):
            summary += "NSX Proxy is connected to CCP.\n"
        else:
            summary += "[WARNING] NSX Proxy is not connected to CCP.\n"

        if self.res.get(CONNECTED_MP) == 3:
            summary += "APH is connected to all three MPAs.\n\n"

        else:
            summary += "[WARNING] APH is not connected some of the three MPAs.\n\n"
        return summary

    def __parse_mgr_netstat(self):
        logging.debug("Parsing  {0}".format(self.file))
        with open(self.file) as f:
            line = f.readline()
            while line:
                if line.find(":1235") > 0:
                    arr = line.split()
                    if arr[3].strip() == "0.0.0.0:1235" and arr[5] == "LISTEN":
                        self.res[CCP_LISTENING] = True
                    elif arr[5] == "ESTABLISHED":
                        if not self.res.get(TN):
                            self.res[TN] = []
                        tn_ip = arr[4].split(":")[0]
                        self.res[TN].append(tn_ip)
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
                        self.res[IP_ADDR] = arr[3].split(":")[0].strip()

                if line.find(":1234") > 0:
                    arr = line.split()
                    if arr[5] == "ESTABLISHED":
                        self.res[CONNECTED_MP] = self.res.get(CONNECTED_MP, 0) + 1
                        self.res[IP_ADDR] = arr[3].split(":")[0].strip()

                line = f.readline()

