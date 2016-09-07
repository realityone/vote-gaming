#!/usr/bin/env python

import contextlib
import logging
import time

import requests
from docker import AutoVersionClient
from flask import Flask
from flask import Response
from flask import render_template
from flask import request

app = Flask(__name__)
client = AutoVersionClient.from_env()

VOTE_IMAGE = 'daocloud.io/realityone/vg-vote'
RESULT_IMAGE = 'daocloud.io/realityone/vg-result'

LOG = logging.getLogger(__name__)


class ReverseProxyUtils(object):

    @classmethod
    def header_matched(cls, name):
        return name in ['User-Agent', 'Host', 'Cookie']

    @classmethod
    def get_headers_from_request(cls, request):
        """
        :type request flask.Request
        """
        return {
            name: value
            for name, value in request.headers
            if cls.header_matched(name)
        }

    @classmethod
    def get_headers_from_response(cls, response):
        """
        :type request flask.Request
        """
        return {
            name: value
            for name, value in response.headers.iteritems()
            if cls.header_matched(name)
        }

    @classmethod
    def get_request_params_from_request(cls, request):
        """
        :type request flask.Request
        """
        return request.args

    @classmethod
    def get_request_data_from_request(cls, request):
        """
        :type request flask.Request
        """
        return request.data or {
            k: v
            for k, v in request.form.iteritems()
        }

    @classmethod
    def convert_to_response(cls, response):
        """
        :type response requests.Response
        """
        return Response(
            response.content,
            headers=cls.get_headers_from_response(response),
            status=response.status_code
        )


def default_container_config():
    return {
        'DEBUG': 'False',
        'SQLALCHEMY_DATABASE_URI': 'mysql+mysqlconnector://root:root@192.168.100.102:3306/vote'
    }


@contextlib.contextmanager
def running_container(image, port, environment=None):
    environment = environment or {}
    host_config = client.create_host_config(port_bindings={port: None})
    response = client.create_container(
        image=image,
        environment=environment,
        ports=[port],
        host_config=host_config
    )
    container_id = response['Id']
    client.start(container_id)

    try:
        yield client.inspect_container(container_id)
    finally:
        client.kill(container_id)
        client.remove_container(container_id)


@app.route('/')
def index():
    return "Hello, World"


@app.route('/vote.html')
def vote_page():
    return render_template('vote.html')


@app.route('/result.html')
def result_page():
    return render_template('result.html')


def make_url(ip, port, path):
    return 'http://{}:{}{}'.format(ip, port, path)


def extract_container_ip(container):
    return container['NetworkSettings']['Ports']


@app.route('/vote', methods=['GET', 'POST'])
@app.route('/result', methods=['GET', 'POST'])
def vote_api():
    def path_to_config():
        path = request.path
        return {
            '/vote': (VOTE_IMAGE, 5000),
            '/result': (RESULT_IMAGE, 5001)
        }[path]

    cfg = default_container_config()
    s = requests.session()
    image, port = path_to_config()
    with running_container(image, port, environment=cfg) as container:
        container_ip = extract_container_ip(container)
        url = make_url(container_ip, port, request.path)
        print url
        response = None
        while True:
            try:
                response = s.request(
                    request.method,
                    url,
                    headers=ReverseProxyUtils.get_headers_from_request(
                        request),
                    allow_redirects=True,
                    params=ReverseProxyUtils.get_request_params_from_request(
                        request),
                    data=ReverseProxyUtils.get_request_data_from_request(
                        request)
                )
            except IOError as e:
                LOG.warning("Request to upstream failed: %s.", e)
            else:
                break
            finally:
                time.sleep(0)

        try:
            response.raise_for_status()
        except Exception as e:
            LOG.error("proxy request error: %s", e)
        finally:
            return ReverseProxyUtils.convert_to_response(response)


if __name__ == '__main__':
    app.run('0.0.0.0', 5003, debug=True)
