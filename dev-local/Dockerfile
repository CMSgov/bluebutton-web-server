FROM python:3.11
ENV PYDEVD_DISABLE_FILE_VALIDATION 1
RUN useradd -m -s /bin/bash DEVLOCAL
USER DEVLOCAL
ADD . /code
WORKDIR /code
RUN python -m venv /tmp/venv
RUN . /tmp/venv/bin/activate
ENV PATH="/tmp/venv/bin:${PATH}"
RUN pip install --upgrade pip
RUN pip install Flask Flask-WTF debugpy
