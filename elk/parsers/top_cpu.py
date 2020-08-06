# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from elk.parsers.custom_parser import CustomParser
from datetime import datetime


class TopCpuParser(CustomParser):
    def __init__(self):
        self.last_timestamp = None

    def process(self, line, timestamp, parse_all=False):
        if line.find("UTC") > 0:
            line = line.strip()
            self.last_timestamp = datetime.strptime(line,
                                                    "%a %b %d %H:%M:%S %Z %Y")
            return

        if line.find("nsx ") > 0:
            res = {'line': line, 'timestamp': timestamp}
            parts = line.split()
            res['cpu'] = float(parts[8])
            res['mem'] = float(parts[9])
            res['timestamp'] = self.last_timestamp
            return res


