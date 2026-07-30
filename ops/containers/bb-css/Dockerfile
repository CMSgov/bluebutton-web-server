FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ENV PYTHONUNBUFFERED=1
ENV PYDEVD_DISABLE_FILE_VALIDATION=1
ENV PYTHON_VERSION=3.12

RUN dnf update -y \
    && dnf install -y \
        nodejs22 \
        nodejs22-npm && dnf clean all && rm -rf /var/cache/dnf

# Add in the codebase
ADD .. /code
WORKDIR /code

# Build the CSS/USWDS assets
CMD ["/code/build-css.bash"]