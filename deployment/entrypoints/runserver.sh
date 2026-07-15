#!/usr/bin/env bash
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
mkdir -p "$PROMETHEUS_MULTIPROC_DIR" && chmod 777 "$PROMETHEUS_MULTIPROC_DIR" && mkdir db
python -m backend.project.manage makemigrations --no-input
python -m backend.project.manage migrate --no-input
python -m backend.project.manage collectstatic --noinput
python -m backend.project.manage init_project_config
python -m backend.project.manage initial_superuser
#python -m backend.project.manage sync_initial_accesses
python -m backend.project.manage runserver