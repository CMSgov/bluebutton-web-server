ARG BUILD_TARGET="local"

FROM amazonlinux:2023.10.20260202.2 AS base

RUN echo "=== COMMON SETUP ==="

# Ensures STDOUT and STDERR do not buffer and 
# flush with every newline so Django logs are captured
# in real-time. 
# Ref: https://stackoverflow.com/a/59812588
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHON_VERSION=3.12
ENV BASE="/home/boton"
ENV BB="${BASE}/bb"
ENV VENVPATH="${BASE}/venv"
ENV PIPBIN="${VENVPATH}/bin"
# TMPDIR could be /dev/shm, too...
ENV NGINX_TMP="/tmp/nginx"

# shadow-utils: for useradd
RUN dnf install -y \
    git \
    nginx \
    python3.12 \
    shadow-utils \
    unzip \
    vim \
    && dnf clean all

# ===== ACTIONS AS ROOT =====
RUN useradd -m -s /bin/bash boton

# Link the nginx.conf to /dev/shm/nginx.conf
# We will put the config there at runtime.
# We create the link at buildtime. We also need to
# make sure that `boton` owns the nginx directories, since we'll
# be running as boton in the container.
RUN chown -R boton:boton /var/lib/nginx \
    && rm /etc/nginx/nginx.conf \
    && ln -s ${NGINX_TMP}/nginx.conf /etc/nginx/nginx.conf

# Route the default nginx logs to stdout/stderr.
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

RUN rm -rf /var/lib/nginx/tmp && ln -s ${NGINX_TMP}/tmp /var/lib/nginx/tmp
RUN ln -s ${NGINX_TMP}/run /run \
    && chown -R boton:boton /run

# ===== ACTIONS AS BOTON =====
USER boton
RUN mkdir -p ${PIPBIN} \
    && mkdir -p ${BB}

# Check out the release tag that we want to build.
ARG RELEASE_TAG="NO_RELEASE_TAG_SET"
WORKDIR ${BB}

# We need a current envsubst for processing the nginx config template.
# The version packaged in Fedora is not new enough.
RUN curl -L -s -o ${PIPBIN}/envsubst https://github.com/a8m/envsubst/releases/download/v1.4.3/envsubst-Linux-x86_64 \
    && chmod +x ${PIPBIN}/envsubst

RUN curl -L -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip > /dev/null 2>&1 \
    && ./aws/install --install-dir ${BB}/aws-cli --bin-dir ${PIPBIN}

FROM base AS build-cloud
RUN echo "=== BUILD FOR LOCAL CONTAINERS ==="
RUN git clone https://github.com/CMSgov/bluebutton-web-server.git . \
    && git fetch --tags \
    && git checkout ${RELEASE_TAG}


FROM base AS build-local
RUN echo "=== BUILD FOR CLOUD DEPLOY ==="
# While running locally, we need to copy ../../.. into the current location.
COPY --chown=boton:boton . .

FROM build-${BUILD_TARGET} AS final
RUN echo "=== FINAL CONFIGURATION ==="

RUN python3.12 -m venv ${VENVPATH} \
    && . ${PIPBIN}/activate \
    && ${PIPBIN}/pip3 install pip==25.3 \
    && ${PIPBIN}/pip3 install pip-tools setuptools

RUN ${PIPBIN}/pip3 install \
    --require-hashes \
    --no-deps \
    --prefer-binary \
    -r requirements/requirements.txt

RUN chmod 755 ${BB}/ops/containers/bb-web-api/entrypoint.bash
# Overwrite the `git_release` file with the current release, so we 
# can work it into our Jinja templates.
RUN rm ${BB}/hhs_oauth_server/settings/git_release.py \
    && echo "GIT_RELEASE = '${RELEASE_TAG}'" > ${BB}/hhs_oauth_server/settings/git_release.py

EXPOSE 8000

CMD ["/home/boton/bb/ops/containers/bb-web-api/entrypoint.bash"]