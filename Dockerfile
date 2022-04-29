FROM python:3.8.10
ENV PYTHONUNBUFFERED 1
# ENV PYTHONDEVMODE 1
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install pip-tools
RUN pip install wheel
RUN make reqs-install-dev
