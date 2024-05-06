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
RUN pip config set global.trusted-host "pypi.org files.pythonhosted.org pypi.python.org"
RUN pip install --upgrade pip-tools
RUN pip install --upgrade setuptools --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org
RUN pip install backports.zoneinfo
RUN pip install charset-normalizer==3.1.0
RUN pip install cryptography==42.0.4
RUN pip install debugpy==1.6.7 --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org
RUN pip install newrelic==8.8.0
RUN pip install pillow==10.3.0
RUN pip install pyyaml==6.0.1
RUN pip install wrapt==1.15.0
RUN pip install -r requirements/requirements.dev.txt --no-index --find-links ./vendor/
