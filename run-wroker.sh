#!/bin/bash
celery -A make_celery worker --loglevel INFO -c 1