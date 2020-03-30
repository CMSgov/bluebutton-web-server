FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN make reqs-install
RUN pip install pip-tools
RUN pip install psycopg2
RUN pip install httmock
