#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json
import time
import os

def parse_url_query(query):
    return dict(e.split('=') for e in query.split('&'))

class Service:
    def __init__(self):
        self.drivers = {}

    def process_get(self, query):
        print("process get ", query)
        client = query['client']
        if (client == 'driver'):
            return self.__get_driver_data(query)

        return None

    def process_post(self, query, data):
        print("process post", query, data)
        success = False

        client = query['client']
        if (client == 'driver'):
            success = self.__post_driver_data(query, data)

        return success

    def __get_driver_data(self, query):
        driver_id = query['id']
        desc = self.drivers.get(driver_id)
        if desc is None:
            return None

        if time.time() - desc['time'] > 30.0:
            return None

        route = desc['route']
        if not route:
            return None

        return route

    def __post_driver_data(self, query, data):
        driver_id = query['id']
        pos = data['pos']
        desc = self.__get_or_create_driver_desc(driver_id)
        desc['route'] = (float(pos[0]), float(pos[1]))
        desc['time'] = time.time()

        return True

    def __get_or_create_driver_desc(self, driver_id):
        desc = self.drivers.get(driver_id)
        if desc is None:
            desc = self.drivers[driver_id] = {
                'route': None,
                'time': 0
            }

        return desc

class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if not parsed_path.query:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(open("index.html").read().encode())
            return

        query = parse_url_query(parsed_path.query)

        global g_service
        data = g_service.process_get(query)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({
            'result': data,
        }).encode())
        return

    def do_POST(self):
        content_len = int(self.headers.get('content-length'))
        post_body = self.rfile.read(content_len)
        data = json.loads(post_body)
        parsed_path = urlparse(self.path)
        query = parse_url_query(parsed_path.query)

        global g_service
        success = g_service.process_post(query, data)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({
            'result': success,
        }).encode())
        return

if __name__ == '__main__':
    g_service = Service()
    server = HTTPServer(('0.0.0.0', 8000), RequestHandler)
    print('Starting server at http://0.0.0.0:8000')
    server.serve_forever()
