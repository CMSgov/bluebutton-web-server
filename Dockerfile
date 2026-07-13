FROM --platform=linux/amd64 python:3.12
ENV PYTHONUNBUFFERED 1
ENV PYDEVD_DISABLE_FILE_VALIDATION 1
RUN apt-get update && apt-get install -y gettext liblcms2-2=2.16-2+deb13u2 libgnutls30t64=3.8.9-3+deb13u4 libssh2-1t64=1.11.1-1+deb13u1 python3.13=3.13.5-2+deb13u3
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
