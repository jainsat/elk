# Copyright (C) 2020 VMware, Inc.  All rights reserved.

import requests
import json
import logging

from string import Template
import pprint
class ELKApi:

    def __init__(self):
        self.hostname = "localhost"
        self.port = "5601"

    def create_space(self, space_name):
        url = "http://{0}:{1}/api/spaces/space".format(self.hostname, self.port)
        payload = {"id": space_name.lower(), "name": space_name}
        headers = {
            'kbn-xsrf': 'reporting',
            'Content-Type': 'text/plain'
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code != 200 and response.status_code != 409:
            print(response.text.encode('utf8'))
            exit(1)

        # Space created successfully (200) or space already existed (409).
        logging.debug("Created space successfully: " + space_name)

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
            url = "http://{0}:{1}/api/saved_objects/index-pattern/{3}" \
                .format(self.hostname, self.port)

        payload = {"attributes": {"title":  index_pattern}}
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

    def create_markdown(self, title, text, space_name=None):
        text = text.replace('\n','\\\\n')
        print ("*********************************** TEXT *****************************************")
        print(text)
        # payload = {
        #     "attributes": {
        #         "title": title,
        #         "visState": "{\"type\":\"markdown\",\"aggs\":[],\"params\":{\"fontSize\":11,\"openLinksInNewTab\":false,\"markdown\":\"" + text +"\"},\"title\": \"" + title + "\"}",
        #         "uiStateJSON": "{}",
        #         "description": "",
        #         "version": 1,
        #         "kibanaSavedObjectMeta": {
        #             "searchSourceJSON": "{\"query\":{\"query\":\"\",\"language\":\"kuery\"},\"filter\":[]}"
        #         }
        #     },
        #     "references": [],
        #     "migrationVersion": {
        #         "visualization": "7.8.0"
        #     }
        # }

        with open('elk/resources/summary.json') as f:
            t = Template(f.read())
            payload = t.substitute(TITLE=title, TEXT=text)
            print(payload)
            print("**************")

        return self.create_ui(payload, "visualization", space_name)










ELKApi().delete_data("Bob")