ARG BUILD_TARGET="local"
ARG RELEASE_TAG="NO_RELEASE_TAG_SET"

FROM amazonlinux:2023.10.20260202.2 AS base

# Ensures STDOUT and STDERR do not buffer and 
# flush with every newline so Django logs are captured
# in real-time. 
# Ref: https://stackoverflow.com/a/59812588
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
# `nginx` wants a temp space; we mount `/tmp` as writeable
# in the production environment.
ENV NGINX_TMP="/tmp/nginx"
# We run nginx in front of the app for HTTPS termination.
EXPOSE ${GUNICORN_PORT}
EXPOSE ${NGINX_PORT}

# shadow-utils: for useradd
RUN dnf install -y \
    git \
    nginx \
    python3.12 \
    shadow-utils \
    unzip \
    vim

#################################################################
# ACTIONS TAKEN AS ROOT USER
RUN useradd -m -s /bin/bash boton

# We will run nginx as the boton user.
# Make sure boton owns everything nginx installed.
RUN chown -R boton:boton /var/lib/nginx

# We will put the config file in /tmp. This gets mounted
# at run time. Therefore, we should remove the default config,
# and link the location from /etc/nginx into /tmp.
# The config itself is populated by entrypoint.bash.
RUN rm /etc/nginx/nginx.conf \
    && ln -s ${NGINX_TMP}/nginx.conf /etc/nginx/nginx.conf

# Route the default nginx logs to stdout/stderr.
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

# nginx would like to write to /var/lib/nginx/tmp.
# That should be linked to a path in /tmp, created at 
# runtime by the entrypoint.
RUN rm -rf /var/lib/nginx/tmp && ln -s ${NGINX_TMP}/tmp /var/lib/nginx/tmp

# nginx wants to write to /run.
# That should be linked into /tmp, and the path
# needs to be writable by boton.
RUN ln -s ${NGINX_TMP}/run /run \
    && chown -R boton:boton /run

#################################################################
# ACTIONS TAKEN AS BOTON USER
USER boton

# Make a path for us to check code out into 
# in boton's home directory
RUN mkdir -p ${BB}
WORKDIR ${BB}

# We abuse the pip `bin` directory for all
# binaries that boton might want to use.
RUN mkdir -p ${BOTONBIN}

# We need a current envsubst for processing the nginx config template.
# The version packaged in Fedora is not new enough.
RUN curl -L -s -o ${BOTONBIN}/envsubst https://github.com/a8m/envsubst/releases/download/v1.4.3/envsubst-Linux-x86_64 \
    && chmod +x ${BOTONBIN}/envsubst

RUN curl -L -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip > /dev/null 2>&1 \
    && ./aws/install --install-dir ${BB}/aws-cli --bin-dir ${BOTONBIN}


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
FROM base AS build-production
RUN git clone -depth 1 https://github.com/CMSgov/bluebutton-web-server.git . \
    && git fetch --tags \
    && git checkout ${RELEASE_TAG}

# The cloud environment only installs the core requirements.
WORKDIR ${BB}
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
COPY --chown=boton:boton . .
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
RUN chmod 755 ${BB}/ops/containers/bb-web-api/scripts/internal/entrypoint.bash
CMD [ "/home/boton/bb/ops/containers/bb-web-api/scripts/internal/entrypoint.bash" ]
