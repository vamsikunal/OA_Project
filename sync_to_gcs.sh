#!/usr/bin/env bash
# =============================================================================
# sync_to_gcs.sh  —  Continuous incremental sync of results/ to GCS
#
# Designed to run as a background daemon alongside the experiment scripts.
# Features:
#   - Incremental sync (gsutil rsync, only changed/new files uploaded)
#   - Exponential back-off on failure (up to MAX_BACKOFF_S seconds)
#   - Low overhead: syncs every SYNC_INTERVAL_S seconds (default 60)
#   - Logs to logs/sync_<timestamp>.log
#   - Graceful shutdown on SIGTERM / SIGINT (flushes one final sync)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — override via environment variables
# ---------------------------------------------------------------------------
GCS_BUCKET="${GCS_BUCKET:-gs://your-rcpsp-results-bucket}"  # MUST be set
RESULTS_DIR="${RESULTS_DIR:-./results}"
LOG_DIR="${LOG_DIR:-./logs}"
SYNC_INTERVAL_S="${SYNC_INTERVAL_S:-60}"     # seconds between sync cycles
MAX_BACKOFF_S="${MAX_BACKOFF_S:-300}"         # max wait after repeated failures
GSUTIL="${GSUTIL:-gsutil}"

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
if [[ "${GCS_BUCKET}" == "gs://your-rcpsp-results-bucket" ]]; then
    echo "[ERROR] GCS_BUCKET is not set. Export it before running:"
    echo "        export GCS_BUCKET=gs://<your-bucket-name>"
    exit 1
fi

if ! command -v "${GSUTIL}" &>/dev/null; then
    echo "[ERROR] gsutil not found. Install the Google Cloud SDK first."
    exit 1
fi

mkdir -p "${LOG_DIR}"

SYNC_LOG="${LOG_DIR}/sync_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "${SYNC_LOG}") 2>&1

echo "============================================================"
echo "  GCS Sync Daemon"
echo "  Started        : $(date)"
echo "  Local source   : ${RESULTS_DIR}"
echo "  GCS destination: ${GCS_BUCKET}/results"
echo "  Interval       : ${SYNC_INTERVAL_S}s"
echo "  Log            : ${SYNC_LOG}"
echo "============================================================"

# ---------------------------------------------------------------------------
# Graceful shutdown: do one final sync before exiting
# ---------------------------------------------------------------------------
final_sync() {
    echo ""
    echo "[SYNC]  Signal received — performing final sync before exit..."
    "${GSUTIL}" -m rsync -r -d \
        "${RESULTS_DIR}" \
        "${GCS_BUCKET}/results" \
        && echo "[SYNC]  Final sync complete." \
        || echo "[WARN]  Final sync failed."
    exit 0
}
trap final_sync SIGTERM SIGINT

# ---------------------------------------------------------------------------
# Main sync loop
# ---------------------------------------------------------------------------
backoff=5
failures=0

while true; do
    sync_start=$(date +%s)
    echo "[SYNC]  $(date '+%Y-%m-%d %H:%M:%S')  Starting incremental sync..."

    set +e
    "${GSUTIL}" -m rsync \
        -r \
        -x '.*\.log$' \
        "${RESULTS_DIR}" \
        "${GCS_BUCKET}/results"
    gsutil_exit=$?
    set -e

    sync_end=$(date +%s)
    elapsed=$(( sync_end - sync_start ))

    if [[ ${gsutil_exit} -eq 0 ]]; then
        echo "[SYNC]  Sync OK  (${elapsed}s)"
        failures=0
        backoff=5   # reset back-off on success
        sleep "${SYNC_INTERVAL_S}"
    else
        failures=$(( failures + 1 ))
        # Exponential back-off: 5, 10, 20, 40, ... capped at MAX_BACKOFF_S
        backoff=$(( backoff * 2 ))
        (( backoff > MAX_BACKOFF_S )) && backoff=${MAX_BACKOFF_S}
        echo "[WARN]  Sync FAILED (attempt ${failures}, exit=${gsutil_exit}). " \
             "Retrying in ${backoff}s..."
        sleep "${backoff}"
    fi
done
