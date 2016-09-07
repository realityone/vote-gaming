FROM daocloud.io/python:2.7.12

RUN pip install tornado && \ 
    pip install sqlalchemy && \
    pip install http://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.zip

ADD ./result.py /result.py
RUN chmod +x result.py

CMD ["/result.py"]