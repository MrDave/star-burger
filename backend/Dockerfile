FROM python:3.10-slim

WORKDIR /opt/star-burger/
RUN apt update && \
    apt install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN --mount=type=bind,source=./requirements.txt,target=/tmp/requirements.txt \
    pip install -r /tmp/requirements.txt --no-cache-dir
COPY src .
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8080", "star_burger.wsgi:application"]