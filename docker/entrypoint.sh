#!/bin/sh

uv run manage.py start_tasks &
uv run gunicorn stave.wsgi:application --bind 0.0.0.0:8888
