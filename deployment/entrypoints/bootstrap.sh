#!/bin/sh
set -eu

MANAGE="python -m dealio.project.manage"
MAX_ATTEMPTS="${DJANGO_MIGRATION_MAX_ATTEMPTS:-30}"
RETRY_DELAY="${DJANGO_MIGRATION_RETRY_DELAY:-2}"
ATTEMPT=1

printf '%s\n' "Applying database migrations..."
until $MANAGE migrate --noinput; do
  if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
    printf '%s\n' "Database migration failed after ${MAX_ATTEMPTS} attempts." >&2
    exit 1
  fi

  printf '%s\n' "Database is not ready; retrying migration (${ATTEMPT}/${MAX_ATTEMPTS})..." >&2
  ATTEMPT=$((ATTEMPT + 1))
  sleep "$RETRY_DELAY"
done

# sample_db already initializes roles, accesses, and project configuration.
$MANAGE sample_db
$MANAGE initial_superuser

case "${SEED_DEMO_COURSES:-false}" in
  1|true|TRUE|yes|YES|on|ON)
    $MANAGE seed_demo_courses
    ;;
esac

$MANAGE collectstatic --noinput

printf '%s\n' "Dealio bootstrap completed successfully."
