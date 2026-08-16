FROM debian:12-slim

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/weewx-venv
ENV PATH="/opt/weewx-venv/bin:$PATH"
RUN pip install --upgrade pip && pip install weewx

WORKDIR /app
CMD ["weewxd", "/app/config/weewx.conf"]