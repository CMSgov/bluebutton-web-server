FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install -r requirements/requirements.dev.txt
RUN pip install psycopg2
