FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYDEVD_DISABLE_FILE_VALIDATION=1
ENV PYTHON_VERSION=3.12

RUN apt-get update \
    && apt-get install -y \
        nodejs \
        npm

# Add in the codebase
ADD .. /code
WORKDIR /code

# Build the CSS/USWDS assets
CMD ["/code/build-css.bash"]