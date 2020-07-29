# Copyright (C) 2020 VMware, Inc.  All rights reserved.


class CustomParser:
    '''
    This is called before the starting of processing of every file.
    It's implementation can return a dictionary, which will be indexed in
    Elasticsearch.
    '''
    def pre(self):
        pass

    '''
    This is called after all the lines of a file have been processed.
    It's implementation can return a dictionary, which will be indexed in 
    Elasticsearch.
    '''
    def post(self):
        pass

    '''
    This is called when all the files are processed.
    It's implementation can return a dictionary, which will be indexed in 
    Elasticsearch.
    '''
    def finish(self):
        pass

    '''
    This is called for every line. It should add key value pairs in the
    dictionary @res which is passed as a parameter. This dictionary will
    have some basic key-value pairs available like ip_address, uuid, filename,
    timestamp associated with the line etc. This method can return a
    dictionary or a list of dictionary. It can also choose to return nothing if
    no relevant data was found in the line.
    '''
    def process(self, line, res):
        pass
