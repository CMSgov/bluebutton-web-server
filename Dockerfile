FROM python:3.7.10
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install --upgrade pip
RUN pip install pip-tools
RUN make reqs-install-dev
RUN pip install debugpy
