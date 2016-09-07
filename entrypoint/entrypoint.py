#!/usr/bin/env python

import sys

from docker import AutoVersionClient
from flask import Flask

app = Flask(__name__)
client = AutoVersionClient.from_env()


@app.route('/')
def index():
    return "Hello, World"


@app.route('/vote.html')
def vote():
    return "vote"


@app.route('/result.html')
def result():
    return "result"


if __name__ == '__main__':
    app.run(debug=True)
