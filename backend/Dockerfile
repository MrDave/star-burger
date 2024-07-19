FROM python:3.10-slim

WORKDIR /opt/star-burger
RUN --mount=type=bind,source=./requirements.txt,target=/tmp/requirements.txt \
    pip install --no-cache-dir -r /tmp/requirements.txt
ENTRYPOINT ["python3", "manage.py"]