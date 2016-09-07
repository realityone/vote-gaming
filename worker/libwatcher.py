from __future__ import absolute_import

import logging

import config
import docker
import docker.errors
import etcd

_log = logging.getLogger(__name__)


def get_death_watcher(etcd_url):
    """
    Should always use this function.
    @param etcd_url:
    @type etcd_url: str
    @return:
    @rtype: DeathWatcher
    """
    from urlparse import urlparse

    etcd_url_parts = urlparse(etcd_url)
    etcd_host, etcd_port = etcd_url_parts.hostname, etcd_url_parts.port

    return DeathWatcher(etcd.Client(host=etcd_host, port=etcd_port),
                        docker.AutoVersionClient.from_env())


class DeathWatcher(object):
    def __init__(self, etcd_client, docker_client, containers_dir=config.CONTAINERS_DIR):
        """
        @param etcd_client: Etcd Client
        @type etcd_client: etcd.Client
        @param docker_client: Swarm Client
        @type docker_client: docker.Client
        """
        self.etcd_client = etcd_client
        self.docker_client = docker_client
        self._containers_dir = containers_dir

        # ensure containers dir exists
        self.ensure_dir()

    def ensure_dir(self):
        try:
            self.etcd_client.get(self._containers_dir)
        except etcd.EtcdKeyNotFound:
            self.etcd_client.write(self._containers_dir, value=None, dir=True, prevExist=False)

    def inspect_container(self, container_id):
        return self.docker_client.inspect_container(container_id)

    def container_key(self, container_id):
        return self._containers_dir + container_id

    def watch_containers(self, timeout=None):
        """
        @param timeout:
        @return:
        @rtype etcd.EtcdResult
        """
        while True:
            o = self.etcd_client.watch(self._containers_dir, timeout=timeout, recursive=True)
            if o:
                yield o

    def refresh_container_ttl(self, container_id, ttl=10):
        try:
            container = self.docker_client.inspect_container(container_id)
        except docker.errors.NotFound:
            _log.error("Container %s not found, maybe has been deleted.")
            return

        key = self.container_key(container.get('Id'))
        try:
            etcd_obj = self.etcd_client.get(key)

            _log.debug("Container is found in etcd, will refresh his ttl.")

            etcd_obj.value, etcd_obj.ttl = container, ttl + etcd_obj.ttl
            etcd_obj = self.etcd_client.update(etcd_obj)
        except etcd.EtcdKeyNotFound:
            _log.debug("Container not found in etcd, will create it first.")

            etcd_obj = self.etcd_client.set(key, container, ttl=ttl)

        return etcd_obj

    def pause_container(self, container_id):
        return self.docker_client.pause(container=container_id)

    def unpause_container(self, container_id):
        container_data = self.docker_client.inspect_container(container_id)
        if container_data.get('State', {}).get('Status') == 'paused':
            return self.docker_client.unpause(container=container_id)
        else:
            _log.debug("Container is already running, skip this event.")

    def stop_container(self, container_id):
        return self.docker_client.stop(container_id)

    def start_container(self, container_id):
        return self.docker_client.start(container_id)
