#!/usr/bin/env python

import os
import json

from tornado import web
from tornado import gen
from tornado import ioloop
from tornado import options
from tornado import httpserver

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base

define = options.define


def row_to_dict(row):
    for column in row.__table__.columns:
        yield column.name, getattr(row, column.name)


class AppConfig(object):

    @staticmethod
    def clean_url(base_url):
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        return base_url

    @staticmethod
    def str2bool(v):
        if v is None:
            return v
        return v.lower() in ('yes', 'true', 't', '1')

    @staticmethod
    def str2int(v):
        try:
            return int(v)
        except:
            return None

    def __init__(self):
        self.address = os.getenv('ADDRESS', '0.0.0.0')
        self.port = self.str2int(os.getenv('PORT', '5000'))
        self.debug = self.str2bool(os.getenv('DEBUG', 'True'))
        self.sqlalchemy_databse_uri = os.getenv(
            'SQLALCHEMY_DATABASE_URI',
            'mysql+mysqlconnector://root:root@127.0.0.1:3306/vote'
        )
        self.database_timezone = os.getenv('DATABASE_TIMEZONE', '+0:00')

config = AppConfig()

engine = create_engine(
    config.sqlalchemy_databse_uri,
    convert_unicode=True,
    pool_recycle=3600,
    echo=config.debug,
    connect_args={
        'time_zone': config.database_timezone
    }
)
Session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.__table_args__ = {
    'mysql_charset': 'utf8',
    'mysql_engine': 'InnoDB'
}
Base.__iter__ = row_to_dict
Base.db = Session


def ensure_schema():
    global Base
    global Session

    Base.metadata.create_all(bind=engine)

    db = Session()

    a = Voting(name='option_a')
    b = Voting(name='option_b')
    db.merge(a)
    db.merge(b)
    db.commit()


class Voting(Base):
    __tablename__ = 'votings'

    name = Column(String(length=255), primary_key=True)
    count = Column(Integer(), nullable=False, default=0)

    @classmethod
    def query_by_names(cls, names):
        return cls.db().query(cls).filter(
            cls.name.in_(names)
        ).all()

    @classmethod
    def increase_option(cls, name, count=1):
        cls.db().query(cls).filter(
            cls.name == name
        ).update({'count': cls.count + count})

    @classmethod
    def query_by_name(cls, name):
        cls.db().query(cls).filter(
            cls.name == name
        ).first()


class BaseHandler(web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    def write_json(self, data):
        json_data = json.dumps(data)
        self.set_header('Content-Type', 'application/json')
        self.finish(json_data)

    def on_finish(self):
        self.db.close()

    @property
    def db(self):
        return self.application.session()


class IndexHandler(BaseHandler):

    def get(self, *args, **kwargs):
        self.write_json({'name': 'vote'})


class VoteHandler(BaseHandler):

    def post(self, *args, **kwargs):
        option = self.get_body_argument('option')

        Voting.increase_option(option)
        self.db.commit()

        self.write_json({})


class Application(web.Application):

    def __init__(self, debug=True):
        global Session
        handlers = [
            ('/', IndexHandler),
            ('/vote', VoteHandler),
        ]
        settings = {
            'debug': debug,
        }
        self.session = Session
        super(Application, self).__init__(handlers, **settings)


def main():
    global config

    ensure_schema()
    http_server = httpserver.HTTPServer(Application(debug=config.debug))
    http_server.listen(config.port, address=config.address)
    ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
