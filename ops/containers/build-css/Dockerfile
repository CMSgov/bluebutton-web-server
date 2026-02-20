FROM python:3.12-trixie

ENV PYTHONUNBUFFERED=1
ENV PYDEVD_DISABLE_FILE_VALIDATION=1
ENV PYTHON_VERSION=3.12

# WARNING
# This is installing the most recent version of Postgres tools.
# We would rather install v16, to match the database, which matches Amazon.
RUN apt-get update \
    && apt-get install -y \
        nodejs \
        npm

# Add in the codebase
ADD .. /code
WORKDIR /code
# Build the CSS/USWDS assets
CMD ["/code/dev-local/build-css.bash"]