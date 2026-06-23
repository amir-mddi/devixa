#!/bin/sh
python -m dealio.project.manage makemigrations
python -m dealio.project.manage migrate --no-input
python -m dealio.project.manage sample_db
python -m dealio.project.manage initial_superuser
#python -m dealio.project.manage sync_initial_accesses
python -m dealio.project.manage collectstatic --noinput
exec "$@"