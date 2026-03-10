ARG BUILD_TARGET="local"
ARG RELEASE_TAG="NO_RELEASE_TAG_SET"
FROM public.ecr.aws/amazonlinux/amazonlinux:2023 AS base
# BUILD ARGS ARE STRANGE
# Note the scoping rules if you want to use them inside a FROM.
# https://docs.docker.com/reference/dockerfile#understand-how-arg-and-from-interact
ARG BUILD_TARGET
ARG RELEASE_TAG

# Ensures STDOUT and STDERR do not buffer and 
# flush with every newline so Django logs are captured
# in real-time. 
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHON_VERSION=3.12

# The application runs as the `boton` user
ENV BASE="/home/boton"
# The code is checked out into the path ~/bb
ENV BB="${BASE}/bb"
# We will set up a venv in the home directory for the app,
# adjacent to the code checkout.
ENV VENVPATH="${BASE}/venv"
# The venv bin directory will get used for other binaries, 
# in addition to what `pip` installs. This way, we only have one
# path we have to bring into the environment.
ENV BOTONBIN="${VENVPATH}/bin"
# We run nginx in front of the app for HTTPS termination.
EXPOSE ${GUNICORN_PORT}

# shadow-utils: for useradd
RUN dnf install -y \
    awscli \
    procps-ng \
    python3.12 \
    shadow-utils

#################################################################
# ACTIONS TAKEN AS ROOT USER
RUN useradd -m -s /bin/bash boton

#################################################################
# ACTIONS TAKEN AS BOTON USER
USER boton

# Make a path for us to check code out into 
# in boton's home directory
RUN mkdir -p ${BB}
WORKDIR ${BB}

# Copy the code in
COPY --chown=boton:boton . .

# We abuse the pip `bin` directory for all
# binaries that boton might want to use.
RUN mkdir -p ${BOTONBIN}

# Activate the venv we run from, and bring our installation
# tools up to the most current versions.
RUN python3.12 -m venv ${VENVPATH} \
    && . ${BOTONBIN}/activate \
    && ${BOTONBIN}/pip3 install --upgrade pip \
    && ${BOTONBIN}/pip3 install pip-tools setuptools

#################################################################
# BUILD FOR CLOUD CONTAINERS
# When we build the production container, we want to check out the repo
# and then checkout the correct release tag.
# https://stackoverflow.com/questions/44438637/arg-substitution-in-run-command-not-working-for-dockerfile
FROM base AS build-production

# The cloud environment only installs the core requirements.
RUN ${BOTONBIN}/pip3 install \
    --require-hashes \
    --no-deps \
    --prefer-binary \
    -r requirements/requirements.txt


#################################################################
# BUILD FOR LOCAL CONTAINERS
# When building a local container for dev, we want to use the 
# code in the developer's tree. The docker context needs to be 
# set to the root of the repo.
FROM base AS build-local
# Only install socat if we are building the local container.
USER root
RUN dnf install -y \
    openssl \
    socat \
    tree
USER boton

# Local dev brings in additional tools to support debugging, etc.
WORKDIR ${BB}
RUN ${BOTONBIN}/pip3 install \
    --require-hashes \
    --no-deps \
    --prefer-binary \
    -r requirements/requirements.dev.txt

#################################################################
# COMMON BUILD FINALIZATION
# Regardless of where the code came from, we now need to install
# all of the dependencies and launch Blue Button.
FROM build-${BUILD_TARGET} AS final
ARG BUILD_TARGET
ARG RELEASE_TAG

# Before leaving, clean up the installation bits.
# Must be done as root.
USER root
RUN dnf clean all
USER boton

# Write out a git release variable matching our release tag.
RUN rm -f ${BB}/hhs_oauth_server/settings/git_release.py \
    && echo "GIT_RELEASE = '${RELEASE_TAG}'" > ${BB}/hhs_oauth_server/settings/git_release.py

# Make sure the entrypoint is executable.
# Default to the production entrypoint.
RUN chmod 755 ${BB}/ops/containers/bb-api/scripts/internal/entrypoint.bash
CMD [ "/home/boton/bb/ops/containers/bb-api/scripts/internal/entrypoint.bash" ]
