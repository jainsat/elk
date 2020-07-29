# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import requests
import json
import logging
from string import Template
import os


class KibanaHandler:
    def __init__(self, host, port):
        self.hostname = host
        self.port = port
        self.vis_count = 0
        self.x = 0
        self.y = 0
        self.root_dir = os.getenv("ELK_REPO")
        with open(os.path.join(self.root_dir, "elk/resources/dashboard.json")) as f:
            self.dashboard_json = json.load(f)

    '''
    Returns true if space creation was successful.
    Returns false if space already existed.
    Raises an exception if space creation failed.
    '''
    def create_space(self, space_name):
        url = "http://{0}:{1}/api/spaces/space".format(self.hostname, self.port)
        payload = {"id": space_name.lower(), "name": space_name}
        headers = {
            'kbn-xsrf': 'reporting',
            'Content-Type': 'text/plain'
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 409:
            return False

        if response.status_code != 200:
            raise Exception(response.text.encode('utf8'))

        # Space created successfully (200) or space already existed (409).
        logging.debug("Created space successfully: " + space_name)

        return True

    def find_index_id(self, index_name, space_name=None):
        space_name = space_name.lower()
        if space_name:
            url = "http://{0}:{1}/s/{2}/api/saved_objects/_find?type="  \
                  "index-pattern&fields=id&fields=title".format(self.hostname,
                                                                self.port,
                                                                space_name)
        else:
            url = "http://{0}:{1}/api/saved_objects/_find?type=" \
                  "index-pattern&fields=id&fields=title".format(self.hostname,
                                                                self.port)

        response = requests.get(url)

        if response.status_code == 200:
            res = response.json()
            saved_objs = res.get("saved_objects")
            for obj in saved_objs:
                if obj.get("attributes").get("title") == index_name:
                    return obj.get("id")

        elif response.status_code == 404:
            return None
        else:
            print(response.text.encode('utf8'))
            exit(1)

    def delete_by_id(self, index_id, type, space_name = None):
        space_name = space_name.lower()
        if space_name:
            url = "http://{0}:{1}/s/{2}/api/saved_objects/{3}/{4}" \
                .format(self.hostname, self.port, space_name, type, index_id)
        else:
            url = "http://{0}:{1}/api/saved_objects/{2}/{3}" \
                .format(self.hostname, self.port, type, id)

        headers = {
            'kbn-xsrf': 'reporting',
            'Content-Type': 'text/plain'
        }

        response = requests.delete(url, headers=headers)
        if response.status_code != 200:
            print(response.text.encode('utf8'))
            exit(1)

    def delete_data(self, space_name = None):
        space_name = space_name.lower()
        types = ["index-pattern", "visualization", "dashboard"]
        for type in types:
            if space_name:
                url = "http://{0}:{1}/s/{2}/api/saved_objects/_find?type=" \
                      "{3}".format(self.hostname, self.port, space_name, type)
            else:
                url = "http://{0}:{1}/api/saved_objects/_find?type=" \
                      "{2}".format(self.hostname, self.port, type)

            response = requests.get(url)

            if response.status_code == 200:
                res = response.json()
                saved_objs = res.get("saved_objects")
                for obj in saved_objs:
                    id = obj.get("id")
                    self.delete_by_id(id, type, space_name)


    def create_index_pattern(self, index_pattern, space_name=None):
        space_name = space_name.lower()
        if space_name:
            url = "http://{0}:{1}/s/{2}/api/saved_objects/index-pattern" \
                .format(self.hostname, self.port, space_name)
        else:
            url = "http://{0}:{1}/api/saved_objects/index-pattern" \
                .format(self.hostname, self.port)

        payload = {"attributes": {"title":  index_pattern, "timeFieldName": "timestamp"}}
        headers = {
            'kbn-xsrf': 'reporting',
            'Content-Type': 'text/plain'
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code != 200:
            print(response.text.encode('utf8'))
            exit(1)

        logging.debug("Index pattern created successfully: " + index_pattern)
        return response.json().get("id")

    def create_ui(self, payload, ui_type, space_name=None):
        space_name = space_name.lower()

        # ui_type can be visualization, dashboard or search.
        if space_name:
            url = "http://{0}:{1}/s/{2}/api/saved_objects/{3}" \
                .format(self.hostname, self.port, space_name, ui_type)
        else:
            url = "http://{0}:{1}/api/saved_objects/{2}" \
                .format(self.hostname, self.port, ui_type)

        headers = {
            'kbn-xsrf': 'reporting',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            print(response.text.encode('utf8'))
            exit(1)

        logging.debug("Visualization created successfully")
        return response.json().get("id")

    def delete_space(self, space_name=None):
        url = "http://{0}:{1}/api/spaces/space/{2}" \
                .format(self.hostname, self.port, space_name.lower())

        headers = {
            'kbn-xsrf': 'reporting',
            'Content-Type': 'text/plain'
        }

        response = requests.delete(url, headers=headers)
        if response.status_code != 204 and response.status_code != 404:
            print(response.text.encode('utf8'))
            exit(1)

    def create_markdown(self, title, text, space_name=None):
        text = text.replace('\n', '\\\\n')
        with open(os.path.join(self.root_dir, 'elk/resources/summary.json')) as f:
            t = Template(f.read())
            payload = t.substitute(TITLE=title, TEXT=text)

        return self.create_ui(payload, "visualization", space_name)

    @staticmethod
    def create_markdown_table(headers, rows):
        text = "|".join(headers) + "\n"

        # This is markdown syntax for defining alignment of column values
        text += "|".join([':-'] * len(headers))

        text += "\n"

        for row in rows:
            text += "|".join(row)
            text += "\n"

        return text

    def create_search(self, title, index, columns, query, space_name=None):
        with open(os.path.join(self.root_dir, 'elk/resources/event_search.json')) as f:
            t = Template(f.read())
            payload = t.substitute(TITLE=title, INDEX= index, COLUMNS=columns,
                                   QUERY=query)
            payload = payload.replace("'", '"')
        return self.create_ui(payload, "search", space_name)

    def add_to_dashboard(self, type, id, height, space_name=None, width=None):

        panels_json = self.dashboard_json.get("attributes").get("panelsJSON")
        with open(os.path.join(self.root_dir, "elk/resources/panel_format.json")) as p:
            panel_format = Template(p.read())
            if width is None:
                width = 23
            if self.x + width > 46:
                self.x = 0
                self.y += 1
            panel_str = panel_format.substitute(X=self.x, Y=self.y,
                                                i=self.vis_count, H=height,
                                                W=width)
            panels_json = panels_json[:-1]
            if self.vis_count > 0:
                panels_json += ", "
            panels_json +=  panel_str + "]"
            self.dashboard_json.get("attributes")["panelsJSON"] = panels_json
            dic = {"name": "panel_" + str(self.vis_count), "type": type,
                   "id": id}
            self.dashboard_json.get("references").append(dic)
            if self.x + width >= 46:
                self.x = 0
                self.y += 1

            else:
                self.x += width

            self.vis_count += 1
            logging.debug(json.dumps(self.dashboard_json))

    def create_dashboard(self, space_name=None):
        self.create_ui(self.dashboard_json, "dashboard", space_name)








# headers = ["Name", "Lunch order", "Spicy", "Owes"]
# rows = [["John", "sandwich", "medium", "$11"],["John", "sandwichdjkfjdkjfkdjfkdjf", "medium", "$11"],["John", "sandwich", "medium", "$11"],["John", "sandwich", "medium", "$11"] ]
# text=KibanaHandler("10.39.1.211", "5601").create_markdown_table(headers, rows)
# print(text)
#KibanaApi().create_search("Events", "3e4305c0-c147-11ea-9597-513cce2a8d77", "Rose")






