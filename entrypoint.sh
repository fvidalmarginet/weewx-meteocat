#!/bin/bash

# Iniciar rsyslog sense intentar llegir el kernel log (/proc/kmsg)
if command -v rsyslogd >/dev/null 2>&1; then
    rsyslogd -m 0
fi

exec "$@"