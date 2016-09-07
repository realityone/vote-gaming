FROM daocloud.io/python:2.7.12-alpine

RUN pip install tornado && \ 
    pip install sqlalchemy && \
    pip install http://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.zip

ADD ./vote.py /vote.py
RUN chmod +x vote.py

CMD ["/vote.py"]

EXPOSE 5000