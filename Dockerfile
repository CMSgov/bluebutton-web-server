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
RUN	pip-compile --generate-hashes --resolver=backtracking --output-file /tmp/requirements.txt requirements/requirements.in
RUN	pip-compile --generate-hashes --resolver=backtracking --output-file /tmp/requirements.dev.txt requirements/requirements.dev.in
RUN mkdir /tmp/vendor
RUN pip install cryptography newrelic PyYAML
RUN pip download -r /tmp/requirements.dev.txt --dest /tmp/vendor --platform linux_x86_64 --no-deps
RUN	pip install -r /tmp/requirements.dev.txt --no-index --find-links /tmp/vendor/

