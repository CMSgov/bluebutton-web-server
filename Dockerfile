FROM python:buster
ENV PYTHONUNBUFFERED 1
# ENV PYTHONDEVMODE 1
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install --upgrade pip
RUN pip install pip-tools
RUN make reqs-install-dev
