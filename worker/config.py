import os

ETCD_URL = os.getenv('ETCD_URL', 'http://192.168.100.102:12379')
DOCKER_HOST = os.getenv('DOCKER_HOST', '')

BASE_DIR = '/death-note/v1'
CONTAINERS_DIR = '/'.join((BASE_DIR, 'containers')) + '/'
