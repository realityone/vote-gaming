FROM daocloud.io/python:2.7.12

ADD ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r /usr/src/app/requirements.txt

ADD . /usr/src/app
WORKDIR /usr/src/app
RUN chmod +x ./main.py

CMD ["./main.py"]
