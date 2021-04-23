#!/usr/bin/env sh

# Start crontab (so it runs jobs in /etc/periodic/*

ME=$(basename $0)

echo "$ME: starting up cron"
crond -L /var/log/crontab
