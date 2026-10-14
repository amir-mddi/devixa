#!/bin/sh
set -eu

PROMETHEUS_MULTIPROC_DIR="${PROMETHEUS_MULTIPROC_DIR:-/tmp/prometheus_multiproc}"
export PROMETHEUS_MULTIPROC_DIR

mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

exec "$@"
