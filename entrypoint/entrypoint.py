#!/usr/bin/env python

import contextlib
import logging
import time

import os
import requests
from docker import AutoVersionClient
from docker.errors import NotFound
from flask import Flask
from flask import Response
from flask import render_template
from flask import request
from flask_cors import CORS

app = Flask(__name__)
client = AutoVersionClient.from_env()

VOTE_IMAGE = 'daocloud.io/realityone/vg-vote'
RESULT_IMAGE = 'daocloud.io/realityone/vg-result'

LOG = logging.getLogger(__name__)
cors = CORS(app)


class AppConfig(object):
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'mysql+mysqlconnector://root:root@192.168.100.102:3306/vote'
    )


class ReverseProxyUtils(object):

    @classmethod
    def header_matched(cls, name):
        return name.lower() in ['user-agent', 'host', 'cookie', 'content-type']

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


def default_container_environment():
    return {
        'DEBUG': 'False',
        'SQLALCHEMY_DATABASE_URI': AppConfig.SQLALCHEMY_DATABASE_URI
    }


@contextlib.contextmanager
def running_container(image, port, name, environment=None):
    environment = environment or {}
    host_config = client.create_host_config(port_bindings={port: None})
    response = client.create_container(
        image=image,
        environment=environment,
        ports=[port],
        host_config=host_config,
        name=name
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
    return container['NetworkSettings']['IPAddress']


@app.route('/vote', methods=['GET', 'POST'])
@app.route('/result', methods=['GET', 'POST'])
def vote_api():
    path_to_config = {
        '/vote': (None, VOTE_IMAGE, 5000),
        '/result': (None, RESULT_IMAGE, 5001)
    }
    path = request.path
    environment = default_container_environment()
    s = requests.session()
    name, image, port = path_to_config[path]

    with running_container(image, port, name, environment=environment) as container:
        container_ip = extract_container_ip(container)
        url = make_url(container_ip, port, path)
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
                        request),
                    timeout=3
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
