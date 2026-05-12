FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ENV PYTHONUNBUFFERED=1
ENV PYDEVD_DISABLE_FILE_VALIDATION=1
ENV PYTHON_VERSION=3.12

RUN dnf update ; dnf install -y \
        gettext \
        gnupg \
        python3.12 \
        which

ADD . /code
WORKDIR /code/requirements

RUN python3.12 -m venv /venv
RUN . /venv/bin/activate
RUN PATH="/venv/bin:${PATH}" \
    pip3.12 install pip==25.3; \
    PATH="/venv/bin:${PATH}" \
    pip3.12 install \
        pip-tools \
        setuptools

CMD ["/code/ops/containers/bb-requirements/scripts/internal/entrypoint.bash"]