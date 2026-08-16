FROM debian:12-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    rsyslog \
    procps \
    && rm -rf /var/lib/apt-lists/*

RUN python3 -m venv /opt/weewx-venv
ENV PATH="/opt/weewx-venv/bin:$PATH"

RUN pip install --no-cache-dir weewx

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]