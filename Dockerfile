FROM --platform=linux/amd64 python:3.11
ENV PYTHONUNBUFFERED 1
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
##RUN pip install cffi==1.16.0 MarkupSafe==2.1.5 jwcrypto==1.5.6 newrelic==8.8.0 pillow==10.3.0 PyYAML==6.0.1
RUN pip install -r requirements/requirements.dev.txt --no-index --find-links ./vendor/