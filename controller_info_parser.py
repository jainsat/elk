# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import logging
import sys
import xml.etree.ElementTree as ET
from log_parser import LogParser
from constants import CONTROLLER_INFO_PATH, CONTROLLER_INFO_PRESENT, \
    MAINTENANCE_MODE, UUID_TN, CONTROLLER1, CONTROLLER2, CONTROLLER3

class Controller:
    def __init__(self, ip, version, uuid):
        self.ip = ip
        self.version = version
        self.uuid = uuid


class ControllerInfoParser(LogParser):

    def __init__(self):
        self.file = None
        self.type = None
        self.res = None

    def init(self, root_dir, res, type=None):
        self.res = res
        self.type = type
        self.file = os.path.join(root_dir, CONTROLLER_INFO_PATH)

    def parse(self):
        # Check if the file exists
        if not self.__is_file_present():
            self.res[CONTROLLER_INFO_PRESENT] = False
            return
        self.res[CONTROLLER_INFO_PRESENT] = True
        root = ET.parse(self.file).getroot()
        if root.find("maintenanceMode") is not None:
            self.res[MAINTENANCE_MODE] = root.find("maintenanceMode").text

        # UUID of transport node.
        self.res[UUID_TN] = root.find("transportNode").find("UUID").text

        # Fetch controller info.
        controllers = root.find("connectionList").findall("connection")
        for i, controller in enumerate(controllers):
            ip = controller.find("server").text
            uuid = controller.find("uuid").text
            version = controller.find("version").text
            self.res["controller{0}".format(i)] = Controller(ip, version, uuid)
        logging.debug(self.res)


    def summarize(self):
        if not self.res[CONTROLLER_INFO_PRESENT]:
            return "Could not find {0}\n".format(self.file)
        with open("templates/controller_info") as f:
            summary = f.read().format(self.file, self.res[UUID_TN],
                           self.res[CONTROLLER1].ip,self.res[CONTROLLER1].version,
                           self.res[CONTROLLER1].uuid, self.res[CONTROLLER2].ip,
                           self.res[CONTROLLER2].version, self.res[CONTROLLER2].uuid,
                           self.res[CONTROLLER3].ip, self.res[CONTROLLER3].version,
                           self.res[CONTROLLER3].uuid)
            if self.res.get(MAINTENANCE_MODE):
                summary = summary + "MaintenanceMode = {0}\n\n".format(self.res[MAINTENANCE_MODE])
            else:
                summary = summary + "MaintenanceMode = NOT FOUND.\n\n"

            return summary


    def __is_file_present(self):

        # if file is not present
        if not os.path.exists(self.file):
            return False

        # If file is empty or whole file has been commented out i.e. not a valid
        # file.
        try:
            tree = ET.parse(self.file)
            return True
        except ET.ParseError:
            return False


