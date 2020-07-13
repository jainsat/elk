# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import constants
import os
from summarizer import Summarizer


class TnSummarizer(Summarizer):
    def __init__(self, data, key):
        self.data = data
        self.key = key
        self.root_dir = os.getenv("ELK_REPO")

    def summarize(self):
        arr = self.key.split("#")
        node_type = arr[0]
        val = self.data.get(self.key)

        summary = ""
        # basic
        with open(os.path.join(self.root_dir, "templates/basic")) as f:
            summary = f.read().format(node_type, val.get(constants.SUPPORT_BUNDLE))

        # controller-info
        if val.get(constants.CONTROLLERS):
            with open(os.path.join(self.root_dir, "templates/controller_info")) as f:
                match = [None] * 3
                for i, controller in enumerate(val[constants.CONTROLLERS]):
                    ip = controller.ip
                    certificate = controller.certificate
                    controller_key = "{0}#{1}".format(constants.MGR, ip)
                    actual_controller_data = self.data.get(controller_key)
                    actual_certificate = None
                    if actual_controller_data:
                        actual_certificate = actual_controller_data.get(constants.CERTIFICATE)
                    if actual_certificate is None:
                        match[i] = "UNKNOWN"
                    elif actual_certificate == certificate:
                        match[i] = "YES"
                    else:
                        match[i] = "NO"
                summary += f.read().format(val.get(constants.UUID),
                                      val[constants.CONTROLLERS][0].ip,
                                      val[constants.CONTROLLERS][0].version,
                                      val[constants.CONTROLLERS][0].uuid,
                                      match[0],
                                      val[constants.CONTROLLERS][1].ip,
                                      val[constants.CONTROLLERS][1].version,
                                      val[constants.CONTROLLERS][1].uuid,
                                      match[1],
                                      val[constants.CONTROLLERS][2].ip,
                                      val[constants.CONTROLLERS][2].version,
                                      val[constants.CONTROLLERS][2].uuid,
                                      match[2],
                                      val.get(constants.MAINTENANCE_MODE))

        # netstat
        with open(os.path.join(self.root_dir, "templates/netstat_tn_summary")) as f:
            summary += f.read().format(val.get(constants.IP_ADDR),
                                  val.get(constants.PROXY_CCP_CONN),
                                  val.get(constants.APH_MPA_CONN))

        # Proxy version
        with open(os.path.join(self.root_dir, "templates/proxy_version")) as f:
            summary += f.read().format(val.get(constants.PROXY_VERSION))

        summary += " #" + "\n\n"

        return summary