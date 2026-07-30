FROM --platform=linux/amd64 public.ecr.aws/amazonlinux/amazonlinux:2023
ENV PYTHONUNBUFFERED=1
ENV PYDEVD_DISABLE_FILE_VALIDATION=1
ENV PYTHON_VERSION=3.12

RUN dnf update -y ; dnf install -y \
        gettext \
        python3.12 \
        shadow-utils && dnf clean all && rm -rf /var/cache/dnf

RUN useradd -m -s /bin/bash DEV
USER DEV
ADD . /code
WORKDIR /code
RUN python3.12 -m venv /tmp/venv
RUN . /tmp/venv/bin/activate
ENV PATH="/tmp/venv/bin:${PATH}"
RUN pip3.12 install pip==25.3
RUN pip3.12 install pip-tools setuptools
RUN pip3.12 install \
    --require-hashes \
    --no-deps \
    --prefer-binary \
    -r requirements/requirements.dev.txt
