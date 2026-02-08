FROM --platform=linux/amd64 python:3.12
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
RUN pip install pip==25.3
RUN pip install pip-tools setuptools
RUN pip install \
    --require-hashes \
    --no-deps \
    --prefer-binary \
    -r requirements/requirements.dev.txt
