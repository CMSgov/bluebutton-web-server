FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install pip-tools
RUN make reqs-install-dev
RUN pip install psycopg2
