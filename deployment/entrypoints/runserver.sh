#!/usr/bin/env bash
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
mkdir -p "$PROMETHEUS_MULTIPROC_DIR" && chmod 777 "$PROMETHEUS_MULTIPROC_DIR" && mkdir db
python -m dealio.project.manage makemigrations --no-input
python -m dealio.project.manage migrate --no-input
python -m dealio.project.manage collectstatic --noinput
python -m dealio.project.manage initial_superuser
#python -m dealio.project.manage sync_initial_accesses
python -m dealio.project.manage runserver