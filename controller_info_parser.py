# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import logging
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
        self.__cinfo_file_path = None

    def parse(self, manager_root_dir, res, type=None):
        self.__cinfo_file_path = os.path.join(manager_root_dir, CONTROLLER_INFO_PATH)

        # Check if the file exists
        if not self.__is_file_present():
            res[CONTROLLER_INFO_PRESENT] = False
            return
        res[CONTROLLER_INFO_PRESENT] = True
        root = ET.parse(self.__cinfo_file_path).getroot()
        if root.find("maintenanceMode") is not None:
            res[MAINTENANCE_MODE] = root.find("maintenanceMode").text


        # UUID of transport node.
        res[UUID_TN] = root.find("transportNode").find("UUID").text

        # Fetch controller info.
        controllers = root.find("connectionList").findall("connection")
        for i, controller in enumerate(controllers):
            ip = controller.find("server").text
            uuid = controller.find("uuid").text
            version = controller.find("version").text
            res["controller{0}".format(i)] = Controller(ip, version, uuid)
        logging.debug(res)


    def summarize(self, res):
        if not res[CONTROLLER_INFO_PRESENT]:
            return "Could not find {0}\n".format(self.__cinfo_file_path)
        with open("templates/controller_info") as f:
            summary = f.read().format(self.__cinfo_file_path, res[UUID_TN],
                           res[CONTROLLER1].ip,res[CONTROLLER1].version,
                           res[CONTROLLER1].uuid, res[CONTROLLER2].ip,
                           res[CONTROLLER2].version, res[CONTROLLER2].uuid,
                           res[CONTROLLER3].ip, res[CONTROLLER3].version,
                           res[CONTROLLER3].uuid)
            if res.get(MAINTENANCE_MODE):
                summary = summary + "MaintenanceMode = {0}\n\n".format(res[MAINTENANCE_MODE])
            else:
                summary = summary + "MaintenanceMode = NOT FOUND.\n\n"

            return summary


    def __is_file_present(self):

        # if file is not present
        if not os.path.exists(self.__cinfo_file_path):
            return False

        # If file is empty or whole file has been commented out i.e. not a valid
        # file.
        try:
            tree = ET.parse(self.__cinfo_file_path)
            return True
        except ET.ParseError:
            return False


