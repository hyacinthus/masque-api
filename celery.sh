#!/usr/bin/env bash
celery -A tasks worker -l debug
