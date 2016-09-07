FROM daocloud.io/python:2.7.12-alpine

RUN pip install etcd && \
    pip install docker-py

ADD . /usr/src/app
WORKDIR /usr/src/app
RUN chmod +x ./main.py

CMD ["./main.py"]