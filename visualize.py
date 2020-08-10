# Copyright (C) 2020 VMware, Inc.  All rights reserved.

from summary.bundle_summarizer import BundleSummarizer
import logging
import json
import os
from string import Template

class Visualize:
    def __init__(self, es_handler, kibana_handler, space, index_id, ip_to_data):
        self.es_handler = es_handler
        self.kibana_handler = kibana_handler
        self.space = space
        self.index_id = index_id
        self.ip_to_data = ip_to_data
        self.root_dir = os.getenv("ELK_REPO")
        if self.root_dir is None:
            raise Exception("Please set ELK_REPO env variable.")

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
        columns = ["entity", "ip_address", "uuid", "event", "log_level"]
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

        # if not barrier and not runtime:
        #     # Create a markdown UI.
        #     id = self.kibana_handler.create_markdown("Realization Dump Summary",
        #                                              "#### All okay!!",
        #                                              self.space)
        #     self.kibana_handler.add_to_dashboard("visualization",
        #                                          id,
        #                                          5,
        #                                          space_name=self.space,
        #                                          width=23)
        #     return

        #if barrier:
        barrier_id = self.__create_barrier_realization_ui()
        self.kibana_handler.add_to_dashboard("search",
                                             barrier_id,
                                             23,
                                             space_name=self.space)

        #if runtime:
        runtime_id = self.__create_runtime_realization_ui()
        self.kibana_handler.add_to_dashboard("search",
                                             runtime_id,
                                             23,
                                             space_name=self.space)

    def export_and_import_dashboard(self, exp_dashboard_name,
                                    exp_dash_space):
        old_dashboard_id = self.kibana_handler.find("dashboard",
                                                    exp_dashboard_name,
                                                    exp_dash_space)
        old_dashboard_json = self.kibana_handler.export_dashboard(old_dashboard_id,
                                                                  exp_dash_space)
        old_dashboard = json.dumps(old_dashboard_json)
        old_index_pattern = "test-index-" + exp_dash_space.lower() + "*"
        old_index_id = self.kibana_handler.find("index-pattern",
                                                old_index_pattern,
                                                exp_dash_space)
        new_dashboard = old_dashboard.replace(old_index_id, self.index_id)
        new_dashboard = new_dashboard.replace(old_index_pattern, "test-index-" +
                                              self.space.lower() + "*")
        self.kibana_handler.import_dashboard(new_dashboard, self.space)
        return old_dashboard_json

    def visualize(self, exp_dash_name=None, exp_dash_space=None):
        if exp_dash_space and exp_dash_name:
            old_dashboard = self.export_and_import_dashboard(exp_dash_name,
                                                             exp_dash_space)
            summary_id = None
            for obj in old_dashboard["objects"]:
                if obj.get("attributes").get("title") == "Summary":
                    summary_id = obj.get("id")
                    #print("summary id={0}".format(summary_id))
                    break
            with open(os.path.join(self.root_dir,
                                   'elk/resources/summary.json')) as f:
                t = Template(f.read())
                summary = BundleSummarizer(self.ip_to_data).get_summary()
                summary = summary.replace('\n', '\\\\n')
                payload = t.substitute(TITLE="Summary", TEXT=summary)
                #print(payload)
                self.kibana_handler.update("visualization", summary_id, payload, self.space)

        else:
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

