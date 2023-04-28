FROM python:3.8
ENV PYTHONUNBUFFERED 1
# ENV PYTHONDEVMODE 1
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN echo "PYTHON VER:" ; python --version
RUN pip install --upgrade pip
RUN pip install --upgrade pip-tools
RUN pip install --upgrade setuptools
RUN pip show setuptools
RUN make reqs-install-dev
# ENTRYPOINT ["tail", "-f", "/dev/null"]

