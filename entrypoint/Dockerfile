FROM daocloud.io/python:2.7.12

ADD requirements.txt /usr/src/app/requirements.txt

RUN pip install -r /usr/src/app/requirements.txt

ADD . /usr/src/app

WORKDIR /usr/src/app
CMD ["gunicorn", "-k", "gevent", "-w", "1", "-b", "0.0.0.0:5003", "--access-logfile", "-", "--error-logfile", "-", "entrypoint:app"]

EXPOSE 5003
