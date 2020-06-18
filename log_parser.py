# Copyright (C) 2020 VMware, Inc.  All rights reserved.


class LogParser:
    '''
    All the log parser classes will implement this interface.
    '''
    def parse(self, manager_root_dir, res, type):
        pass

    def summarize(self, res):
        pass
