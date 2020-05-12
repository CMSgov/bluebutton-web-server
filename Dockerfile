FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN apt-get update
RUN apt install -y dos2unix
RUN pip install pip-tools
RUN make reqs-compile
RUN make reqs-download
RUN make reqs-install
RUN pip install psycopg2

