FROM python:3.7.13
ENV PYTHONUNBUFFERED 1
# ENV PYTHONDEVMODE 1
# RUN mkdir /code
RUN useradd -m -s /bin/bash DEV
USER DEV
ADD . /code
WORKDIR /code
RUN python -m venv /tmp/venv
RUN . /tmp/venv/bin/activate
ENV PATH="/tmp/venv/bin:${PATH}"
RUN pip install --upgrade pip
RUN pip install pip-tools
RUN pip install -r ./requirements/requirements.dev.txt --no-index --find-links ./vendor/
