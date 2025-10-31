FROM --platform=linux/amd64 python:3.11
ENV PYTHONUNBUFFERED 1
ENV PYDEVD_DISABLE_FILE_VALIDATION 1
RUN apt-get update && apt-get install -y gettext
RUN useradd -m -s /bin/bash DEV
USER DEV
ADD . /code
WORKDIR /code
RUN wget -P /tmp https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
RUN unzip /tmp/sonar-scanner-cli-5.0.1.3006-linux.zip -d /tmp
RUN python -m venv /tmp/venv
RUN . /tmp/venv/bin/activate
ENV PATH="/tmp/sonar-scanner-5.0.1.3006-linux/bin:/tmp/venv/bin:${PATH}"
RUN pip install --upgrade pip pip-tools setuptools coverage
RUN pip install -r requirements/requirements.dev.txt --no-index --find-links ./vendor/
