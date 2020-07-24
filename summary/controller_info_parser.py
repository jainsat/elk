# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import os
import logging
import xml.etree.ElementTree as ET
from summary.log_parser import LogParser
from constants import CONTROLLER_INFO_PATH, MAINTENANCE_MODE, UUID, \
    CONTROLLERS


class Controller:
    def __init__(self, ip, version, uuid, certificate):
        self.ip = ip
        self.version = version
        self.uuid = uuid
        self.certificate = certificate


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
            logging.debug("Could not find {0}\n".format(self.file))
            return
        root = ET.parse(self.file).getroot()
        if root.find("maintenanceMode") is not None:
            self.res[MAINTENANCE_MODE] = root.find("maintenanceMode").text

        # UUID of transport node.
        self.res[UUID] = root.find("transportNode").find("UUID").text

        # Fetch controller info.
        controllers = root.find("connectionList").findall("connection")
        controller_list = []
        for i, controller in enumerate(controllers):
            ip = controller.find("server").text
            uuid = controller.find("uuid").text
            version = controller.find("version").text
            certificate = controller.find("pemKey").text
            controller_list.append(Controller(ip, version, uuid, certificate))
            logging.debug(self.res)
        self.res[CONTROLLERS] = controller_list

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
