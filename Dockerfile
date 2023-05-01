FROM python:3.8
ENV PYTHONUNBUFFERED 1
# ENV PYTHONDEVMODE 1
RUN useradd -m -s /bin/bash DEV
USER DEV
ADD . /code
WORKDIR /code
RUN python -m venv /tmp/venv
RUN . /tmp/venv/bin/activate
ENV PATH="/tmp/venv/bin:${PATH}"
RUN pip install --upgrade pip
RUN pip install --upgrade pip-tools
RUN pip install --upgrade setuptools
RUN make reqs-install-dev

