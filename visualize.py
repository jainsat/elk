# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from summary.bundle_summarizer import BundleSummarizer
import logging


class Visualize:
    def __init__(self, es_handler, kibana_handler, space, index_id, ip_to_data):
        self.es_handler = es_handler
        self.kibana_handler = kibana_handler
        self.space = space
        self.index_id = index_id
        self.ip_to_data = ip_to_data

    def __create_summary(self):
        # Get summary of logs
        summary = BundleSummarizer(self.ip_to_data).get_summary()

        # Create a markdown UI for summary.
        summary_id = self.kibana_handler.create_markdown("Summary", summary,
                                                         self.space)
        logging.debug("summary id = " + summary_id)
        self.kibana_handler.add_to_dashboard("visualization", summary_id, 23,
                                             space_name=self.space)

    def __create_events_ui(self):
        # Create a search UI for Events
        columns = ["entity", "ip_address", "event", "status"]
        search_id = self.kibana_handler.create_search("Events", self.index_id,
                                                      columns, "event: *",
                                                      self.space)
        logging.debug("events search id = " + search_id)
        self.kibana_handler.add_to_dashboard("search", search_id, 23,
                                             space_name=self.space)

    def __create_barrier_realization_ui(self):

        columns = ["uuid", "tn_uuid", "vertical", "expected_barrier",
                   "processed_barrier"]
        search_id = self.kibana_handler.create_search("Realization Barrier Status",
                                                      self.index_id,
                                                      columns,
                                                      "expected_barrier: *",
                                                      self.space)
        logging.debug("barrier search id = " + search_id)
        return search_id

    def __create_runtime_realization_ui(self):

        columns = ["uuid", "tn_uuid", "component", "err_msg"]
        search_id = self.kibana_handler.create_search("Realization Runtime Status",
                                                      self.index_id,
                                                      columns,
                                                      "component: *",
                                                      self.space)
        logging.debug("runtime search id = " + search_id)
        return search_id

    def __create_realization_ui(self):

        # Check if there is realization related data in Elasticsearch
        barrier = self.es_handler.query("processed_barrier: *")
        runtime = self.es_handler.query("component: *")

        if not barrier and not runtime:
            # Create a markdown UI.
            id = self.kibana_handler.create_markdown("Realization Dump Summary",
                                                     "#### All okay!!",
                                                     self.space)
            self.kibana_handler.add_to_dashboard("visualization",
                                                 id,
                                                 5,
                                                 space_name=self.space,
                                                 width=23)
            return

        if barrier:
            barrier_id = self.__create_barrier_realization_ui()
            self.kibana_handler.add_to_dashboard("search",
                                                 barrier_id,
                                                 23,
                                                 space_name=self.space)

        if runtime:
            runtime_id = self.__create_runtime_realization_ui()
            self.kibana_handler.add_to_dashboard("search",
                                                 runtime_id,
                                                 23,
                                                 space_name=self.space)

    def visualize(self):
        self.__create_summary()
        self.__create_events_ui()
        self.__create_realization_ui()
        self.kibana_handler.create_dashboard(self.space)

    @staticmethod
    def __create_realization_ui_body(barrier_body, runtime_body):
        text = ""
        if barrier_body:
            text = "##### Realization Status\n"
            text += barrier_body
        if runtime_body:
            if text:
                text += "&nbsp;\n##### Runtime Status\n"
                text += runtime_body
        return text

