FROM --platform=linux/amd64 python:3.8
ENV PYTHONUNBUFFERED 1
RUN useradd -m -s /bin/bash DEV
USER DEV
ADD . /code
WORKDIR /code
RUN wget -P /tmp https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
RUN unzip /tmp/sonar-scanner-cli-5.0.1.3006-linux.zip -d /tmp
RUN python -m venv /tmp/venv
RUN . /tmp/venv/bin/activate
ENV PATH="/tmp/sonar-scanner-5.0.1.3006-linux/bin:/tmp/venv/bin:${PATH}"
RUN pip install --upgrade pip
RUN pip install --upgrade pip-tools
RUN pip install --upgrade setuptools
RUN pip install --upgrade coverage
RUN pip install -r requirements/requirements.dev.txt --no-index --find-links ./vendor/