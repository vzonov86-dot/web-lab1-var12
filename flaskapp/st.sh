#!/bin/bash
gunicorn --bind 127.0.0.1:5000 some_app:app & APP_PID=$!
sleep 10
python3 client.py
APP_CODE=$?
kill -TERM $APP_PID
sleep 2
exit $APP_CODE
