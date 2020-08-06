# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import re
from elk.parsers.custom_parser import CustomParser

EXPECTED_BARRIER_SECTION = 0
REALIZATION_STATUS_SECTION = 1
RUNTIME_STATUS_SECTION = 2

UUID_REG = '^[A-Fa-f0-9]{8}-(?:[A-Fa-f0-9]{4}-){3}[A-Fa-f0-9]{12}'
UUID_RE = re.compile(UUID_REG)


class RealizationDumpParser(CustomParser):
    def __init__(self):
        self.section = -1

        # UUID to barrier map.
        self.expected_barrier_map = {}
        self.tn_to_record = {}
        self.tn_to_dump ={}

    def __set_section(self, num):
        self.section = num

    def process(self, line, timestamp, parse_all=False):
        if line.find("Expected barrier for all") == 0:
            self.__set_section(EXPECTED_BARRIER_SECTION)

        if line.find("Realization status for all") == 0:
            self.__set_section(REALIZATION_STATUS_SECTION)

        if line.find("Runtime status for all") == 0:
            self.__set_section(RUNTIME_STATUS_SECTION)

        if self.section == EXPECTED_BARRIER_SECTION:
            match = UUID_RE.search(line)
            if match:
                uuid = match.group(0)
                barrier_id = line.split(":")[1].strip()
                self.expected_barrier_map[uuid] = barrier_id

        if self.section == REALIZATION_STATUS_SECTION:
            match = UUID_RE.search(line)
            if match:
                uuid = match.group(0)
                vertical = line.split()[1].strip()
                processed_barrier = line.split()[2].strip()
                expected_barrier = self.expected_barrier_map.get(uuid)
                res = {'line': line, 'timestamp': timestamp}
                res['tn_uuid'] = uuid
                res['expected_barrier'] = expected_barrier
                res['processed_barrier'] = processed_barrier
                res['vertical'] = vertical
                res['tag'] = 'realization'
                tn_records = self.tn_to_record.get(uuid, [])
                tn_records.append(res)
                self.tn_to_record[uuid] = tn_records
                if processed_barrier != expected_barrier or self.tn_to_dump.get(uuid):
                    self.tn_to_record.pop(uuid)
                    self.tn_to_dump[uuid] = True
                    return tn_records

        if self.section == RUNTIME_STATUS_SECTION:
            match = UUID_RE.search(line)
            if match:
                uuid = match.group(0)
                words = line.split()

                # This means that error message is present.
                if len(words) >= 3:
                    component = words[1].strip()
                    res = {'line': 'line', 'timestamp': timestamp}
                    res['tn_uuid'] = uuid
                    res['component'] = component
                    res['err_msg'] = line[len(component) + len(uuid) + 2:].strip()
                    res['tag'] = 'realization'
                    return res











