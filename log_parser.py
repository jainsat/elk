# Copyright (C) 2020 VMware, Inc.  All rights reserved.


class LogParser:
    '''
    All the log parser classes will implement this interface.
    '''
    def init(self, manager_root_dir, res, type):
        pass

    def parse(self):
        pass
