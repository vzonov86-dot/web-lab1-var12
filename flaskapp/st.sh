#!/bin/bash
gunicorn --bind 127.0.0.1:5000 some_app:app & APP_PID=$!
sleep 5
python client.py
APP_CODE=$?
kill -TERM $APP_PID
exit $APP_CODE
