FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ENV PYTHONUNBUFFERED=1
ENV PYTHON_VERSION=3.12

RUN dnf update -y && dnf install -y python3.12 && dnf clean all && rm -rf /var/cache/dnf

WORKDIR /code

RUN python3.12 -m venv /venv
ENV PATH="/venv/bin:${PATH}"

COPY requirements.txt .
RUN pip3.12 install --no-cache-dir pip==25.3 && \
    pip3.12 install --no-cache-dir -r requirements.txt && \
    pip3.12 install --no-cache-dir debugpy

COPY . .

EXPOSE 8080

CMD ["python3.12", "app.py"]