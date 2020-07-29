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
        return summary_id

    def __create_events_ui(self):
        # Create a search UI for Events
        search_id = self.kibana_handler.create_search("Events", self.index_id,
                                                      self.space)
        logging.debug("search id = " + search_id)
        return search_id

    def __create_realization_barrier_status_body(self, response):
        headers = ["ccp uuid", "tn uuid", "vertical", "expected barrier",
                   "processed barrier"]
        rows = []
        for entry in response:
            row = []
            source = entry.get("_source")
            row.append(source.get("uuid"))
            row.append(source.get("tn_uuid"))
            row.append(source.get("vertical"))
            row.append(source.get("expected_barrier"))
            row.append(source.get("processed_barrier"))
            rows.append(row)
        return self.kibana_handler.create_markdown_table(headers, rows)

    def __create_realization_runtime_status_body(self, response):
        headers = ["ccp uuid", "tn uuid", "component", "err_msg"]
        rows = []
        for entry in response:
            row = []
            source = entry.get("_source")
            row.append(source.get("uuid"))
            row.append(source.get("tn_uuid"))
            row.append(source.get("component"))
            row.append(source.get("err_msg"))
            rows.append(row)
        return self.kibana_handler.create_markdown_table(headers, rows)

    def __create_realization_ui(self):

        # Check if there is realization related data in Elasticsearch
        barrier = self.es_handler.query("processed_barrier: *")
        runtime = self.es_handler.query("component: *")

        if barrier:
            barrier_body = self.__create_realization_barrier_status_body(barrier)

        if runtime:
            runtime_body = self.__create_realization_runtime_status_body(runtime)

        if barrier or runtime:
            final_body = self.__create_realization_ui_body(barrier_body,
                                                           runtime_body)
            height = 14 # height of UI PAN
            width = 46
        else:
            final_body = "## All Okay!!"
            height = 5
            width = 23

        # Create a markdown UI for table.
        table_id = self.kibana_handler.create_markdown("Realization Dump Summary",
                                                       final_body, self.space)
        logging.debug("table id = " + table_id)
        return table_id, height, width

    def visualize(self):
        summary_id = self.__create_summary()
        events_id = self.__create_events_ui()
        realization_id, realization_ui_height, width = \
            self.__create_realization_ui()

        self.kibana_handler.add_to_dashboard("visualization", summary_id, 23,
                                             space_name=self.space)

        self.kibana_handler.add_to_dashboard("search", events_id, 23,
                                             space_name=self.space)

        self.kibana_handler.add_to_dashboard("visualization", realization_id,
                                             realization_ui_height,
                                             space_name=self.space, width=width)

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

