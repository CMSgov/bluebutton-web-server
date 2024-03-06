FROM python:3.8
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
RUN pip install backports-zoneinfo==0.2.1 charset-normalizer==3.1.0 cryptography==41.0.7 debugpy==1.6.7 newrelic==8.8.0 pillow==10.0.1 pyyaml==6.0.1
RUN pip install wrapt==1.15.0
RUN pip install -r requirements/requirements.dev.txt --no-index --find-links ./vendor/
