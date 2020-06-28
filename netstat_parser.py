# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import sys
import logging
from constants import MGR_NETSTAT_PATH, CCP_LISTENING, MGR, ESX, EDGE, KVM_UBU, \
    KVM_UBU_NETSTAT_PATH, PROXY_CCP_CONN, APH_MPA_CONN, ESX_NETSTAT_PATH, \
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
            logging.debug("Found {0}".format(self.file))
        else:
            logging.debug("Could not find {0}.".format(self.file))
        if self.type == MGR or self.type == GLOB_MGR:
            return self.__summarize_mgr()
        else:
            return self.__summarize_tn()

    def __summarize_mgr(self):
        with open("templates/netstat_ccp_summary") as f:
            summary = f.read().format(self.res.get(CCP_LISTENING),
                                      self.res.get(TN))

        return summary

    def __summarize_tn(self):
        with open("templates/netstat_tn_summary") as f:
            summary = f.read().format(self.res.get(IP_ADDR),
                                      self.res.get(PROXY_CCP_CONN),
                                      self.res.get(APH_MPA_CONN))

        return summary


    def __parse_mgr_netstat(self):
        logging.debug("Parsing  {0}".format(self.file))
        self.res[CCP_LISTENING] = "is not"
        with open(self.file) as f:
            line = f.readline()
            while line:
                if line.find(":1235") > 0:
                    arr = line.split()
                    if arr[3].strip() == "0.0.0.0:1235" and arr[5] == "LISTEN":
                        self.res[CCP_LISTENING] = "is"
                    elif arr[5] == "ESTABLISHED":
                        if not self.res.get(TN):
                            self.res[TN] = []
                        tn_ip = arr[4].split(":")[0]
                        self.res[TN].append(tn_ip)
                line = f.readline()

    def __parse_tn_netstat(self):
        logging.debug("Parsing  {0}".format(self.file))
        self.res[PROXY_CCP_CONN] = "is not"
        with open(self.file) as f:
            line = f.readline()
            while line:
                if line.find(":1235") > 0:
                    arr = line.split()
                    if arr[5] == "ESTABLISHED":
                        self.res[PROXY_CCP_CONN] = "is"
                        self.res[IP_ADDR] = arr[3].split(":")[0].strip()

                if line.find(":1234") > 0:
                    arr = line.split()
                    if arr[5] == "ESTABLISHED":
                        self.res[APH_MPA_CONN] = self.res.get(APH_MPA_CONN, 0) + 1
                        self.res[IP_ADDR] = arr[3].split(":")[0].strip()

                line = f.readline()

        if self.res[APH_MPA_CONN] == 3:
            self.res[APH_MPA_CONN] = "is"
        else:
            self.res[APH_MPA_CONN] = "is not"

