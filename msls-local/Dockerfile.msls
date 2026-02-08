FROM python:3.12-trixie

ENV PYTHONUNBUFFERED=1
ENV PYTHON_VERSION=3.12

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir pip==25.3 && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir debugpy

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]