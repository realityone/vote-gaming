#!/usr/bin/env python

import contextlib
import logging
import socket
import time
from urlparse import urlparse

import etcd
import os
import requests
from docker import AutoVersionClient
from docker import errors
from flask import Flask
from flask import Response
from flask import render_template
from flask import request
from flask_cors import CORS

app = Flask(__name__)
client = AutoVersionClient.from_env()

VOTE_IMAGE = 'daocloud.io/alphabeta_com/vg-vote'
RESULT_IMAGE = 'daocloud.io/alphabeta_com/vg-result'

LOG = logging.getLogger(__name__)
cors = CORS(app)

HOST_NAME = socket.gethostname()
PATH_TO_CONFIG = {
    '/vote': ('vg-vote-{}'.format(HOST_NAME), VOTE_IMAGE, 5000),
    '/result': ('vg-result-{}'.format(HOST_NAME), RESULT_IMAGE, 5001)
}


class AppConfig(object):
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'mysql+mysqlconnector://root:root@192.168.100.102:3306/vote'
    )
    ETCD_URL = os.getenv(
        'ETCD_URL',
        'http://192.168.100.102:12379'
    )
    ENV_API = os.getenv(
        'ENV_API',
        '54.238.140.58:8081'
    )
    HOST_IP = os.getenv(
        'HOST_IP',
        '192.168.2.142'
    )
    TTL = 1


etcd_url_parts = urlparse(AppConfig.ETCD_URL)
etcd_client = etcd.Client(host=etcd_url_parts.hostname, port=etcd_url_parts.port)


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
    def death_key(container_id):
        return '/death-note/v1/containers/{}'.format(container_id)

    try:
        container = client.inspect_container(name)
    except errors.NotFound as e:
        LOG.warning("inspect container %s failed: %s, will create it.", name, e)

        environment = environment or {}
        host_config = client.create_host_config(
            port_bindings={port: None},
            restart_policy={
                'Name': 'always'
            }
        )
        try:
            response = client.create_container(
            image=image,
            environment=environment,
            ports=[port],
            host_config=host_config,
            name=name
        )
        except errors.APIError as e:
            LOG.error("Create container failed maybe created by others: %s.", e)
            time.sleep(1)
        else:
            container_id = response['Id']
            client.start(container_id)
        finally:
            container = client.inspect_container(name)

    container_id = container['Id']
    key = death_key(container_id)
    try:
        etcd_obj = etcd_client.get(key)

        LOG.debug("Container is found in etcd, will refresh his ttl.")

        etcd_obj.ttl = AppConfig.TTL + (etcd_obj.ttl or 1)
        try:
            etcd_client.update(etcd_obj)
        except etcd.EtcdCompareFailed as e:
            LOG.debug("Etcd atomic update failed: %s, skip it.", e)
    except etcd.EtcdKeyNotFound:
        LOG.debug("Container not found in etcd, will create it first.")
        etcd_client.set(key, container_id, ttl=AppConfig.TTL)

    yield container


@app.route('/')
def index():
    return render_template('index.html', env_api=AppConfig.ENV_API)


@app.route('/vote.html')
def vote_page():
    return render_template('vote.html')


@app.route('/result.html')
def result_page():
    return render_template('result.html')


def make_url(ip, port, path):
    return 'http://{}:{}{}'.format(ip, port, path)


def extract_container_endpoint(container, port):
    container_ip = container['NetworkSettings']['IPAddress']
    host_port = container['NetworkSettings']['Ports']['{}/tcp'.format(port)][0]['HostPort']
    return container_ip, host_port


@app.route('/vote', methods=['GET', 'POST'])
@app.route('/result', methods=['GET', 'POST'])
def vote_api():
    path = request.path
    environment = default_container_environment()
    s = requests.session()
    name, image, port = PATH_TO_CONFIG[path]

    with running_container(image, port, name, environment=environment) as container:
        _, host_port = extract_container_endpoint(container, port)
        url = make_url(AppConfig.HOST_IP, host_port, path)
        response = None
        while True:
            try:
                response = s.request(
                    request.method,
                    url,
                    headers=ReverseProxyUtils.get_headers_from_request(request),
                    allow_redirects=True,
                    params=ReverseProxyUtils.get_request_params_from_request(request),
                    data=ReverseProxyUtils.get_request_data_from_request(request),
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
