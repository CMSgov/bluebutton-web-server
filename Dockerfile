FROM --platform=linux/amd64 python:3.11
ENV PYTHONUNBUFFERED 1
ENV PYDEVD_DISABLE_FILE_VALIDATION 1
RUN apt-get update && apt-get install -y gettext
RUN useradd -m -s /bin/bash DEV
USER DEV
ADD . /code
WORKDIR /code
RUN python -m venv /tmp/venv
RUN . /tmp/venv/bin/activate
ENV PATH="/tmp/venv/bin:${PATH}"
RUN pip install --upgrade pip pip-tools setuptools
RUN pip install -r requirements/requirements.dev.txt --no-index --find-links ./vendor/
