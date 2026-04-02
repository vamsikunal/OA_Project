#!/usr/bin/env bash
# =============================================================================
# run_non_cpr.sh  —  Sequential non-CPR experiments (standard RCPSP)
#
# Runs up to 240 J30 instances and 120 J60 instances.
# Resume-safe: already-completed instances are skipped automatically.
# Results are written as JSON + a per-run summary CSV.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configurable parameters (override via environment variables if needed)
# ---------------------------------------------------------------------------
INSTANCE_DIR="${INSTANCE_DIR:-./instances}"
RESULTS_DIR="${RESULTS_DIR:-./results}"
LOG_DIR="${LOG_DIR:-./logs}"
PYTHON="${PYTHON:-python3}"
MODEL="${MODEL:-SEQ}"
TIME_LIMIT="${TIME_LIMIT:-500}"
J30_LIMIT="${J30_LIMIT:-240}"    # max J30 instances to run
J60_LIMIT="${J60_LIMIT:-120}"    # max J60 instances to run

RUN_ID="non_cpr_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_DIR}/${RUN_ID}.log"
SUMMARY_CSV="${RESULTS_DIR}/summary_non_cpr.csv"

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
mkdir -p "${RESULTS_DIR}/j30" "${RESULTS_DIR}/j60" "${LOG_DIR}"

# Redirect all output to both terminal and log file
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "============================================================"
echo "  RCPSP Non-CPR Experiment Run"
echo "  Run ID   : ${RUN_ID}"
echo "  Started  : $(date)"
echo "  Model    : ${MODEL}"
echo "  Limit    : J30=${J30_LIMIT}  J60=${J60_LIMIT}"
echo "  Time lmt : ${TIME_LIMIT}s per instance"
echo "============================================================"

# Write CSV header if file does not yet exist
if [[ ! -f "${SUMMARY_CSV}" ]]; then
    echo "run_id,instance,set,status,makespan,runtime_s,mip_gap,timestamp" \
        > "${SUMMARY_CSV}"
fi

# ---------------------------------------------------------------------------
# Helper: run one instance and append result to summary CSV
# ---------------------------------------------------------------------------
run_instance() {
    local instance_path="$1"
    local instance_set="$2"   # j30 or j60
    local instance_name
    instance_name="$(basename "${instance_path}" .sm)"
    local result_file="${RESULTS_DIR}/${instance_set}/${instance_name}_non_cpr.json"

    # Resume-safe: skip if result already exists and is non-empty
    if [[ -s "${result_file}" ]]; then
        echo "[SKIP]  ${instance_name}  (result already exists)"
        return 0
    fi

    echo "[RUN]   ${instance_name}  ..."
    local start_ts
    start_ts=$(date +%s)

    # Run solver; capture JSON output; tolerate non-zero exit (infeasible etc.)
    set +e
    "${PYTHON}" rcpsp_cpr_seq.py \
        --instance  "${instance_path}" \
        --model     "${MODEL}" \
        --time-limit "${TIME_LIMIT}" \
        --output-json "${result_file}" \
        2>&1 | tee -a "${LOG_FILE}"
    local exit_code=$?
    set -e

    local end_ts
    end_ts=$(date +%s)
    local elapsed=$(( end_ts - start_ts ))

    # Parse key fields from JSON for the summary CSV
    local status makespan runtime mip_gap
    if [[ -s "${result_file}" ]]; then
        status=$(python3  -c "import json,sys; d=json.load(open('${result_file}')); print(d.get('status','UNKNOWN'))"  2>/dev/null || echo "PARSE_ERROR")
        makespan=$(python3 -c "import json,sys; d=json.load(open('${result_file}')); print(d.get('makespan',''))"       2>/dev/null || echo "")
        runtime=$(python3  -c "import json,sys; d=json.load(open('${result_file}')); print(d.get('runtime_s',''))"      2>/dev/null || echo "${elapsed}")
        mip_gap=$(python3  -c "import json,sys; d=json.load(open('${result_file}')); print(d.get('mip_gap',''))"        2>/dev/null || echo "")
    else
        status="SOLVER_ERROR"
        makespan=""; runtime="${elapsed}"; mip_gap=""
        # Write a minimal error JSON so the file is non-empty (won't re-run by accident)
        echo '{"status":"SOLVER_ERROR","makespan":null,"runtime_s":'"${elapsed}"',"mip_gap":null}' \
            > "${result_file}"
    fi

    echo "${RUN_ID},${instance_name},${instance_set},${status},${makespan},${runtime},${mip_gap},$(date -Iseconds)" \
        >> "${SUMMARY_CSV}"

    echo "[DONE]  ${instance_name}  status=${status}  makespan=${makespan}  time=${elapsed}s"
}

# ---------------------------------------------------------------------------
# J30 instances
# ---------------------------------------------------------------------------
echo ""
echo "--- J30 instances ---"
j30_count=0
j30_total=0

# Count available instances first for progress display
mapfile -t J30_FILES < <(find "${INSTANCE_DIR}/j30.sm" -name "*.sm" 2>/dev/null | sort)
j30_total=$(( ${#J30_FILES[@]} < J30_LIMIT ? ${#J30_FILES[@]} : J30_LIMIT ))

for instance in "${J30_FILES[@]}"; do
    (( j30_count >= J30_LIMIT )) && break
    j30_count=$(( j30_count + 1 ))
    echo -n "[${j30_count}/${j30_total}] "
    run_instance "${instance}" "j30"
done

# ---------------------------------------------------------------------------
# J60 instances
# ---------------------------------------------------------------------------
echo ""
echo "--- J60 instances ---"
j60_count=0
j60_total=0

mapfile -t J60_FILES < <(find "${INSTANCE_DIR}/j60.sm" -name "*.sm" 2>/dev/null | sort)
j60_total=$(( ${#J60_FILES[@]} < J60_LIMIT ? ${#J60_FILES[@]} : J60_LIMIT ))

for instance in "${J60_FILES[@]}"; do
    (( j60_count >= J60_LIMIT )) && break
    j60_count=$(( j60_count + 1 ))
    echo -n "[${j60_count}/${j60_total}] "
    run_instance "${instance}" "j60"
done

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Run complete : $(date)"
echo "  J30 processed: ${j30_count}"
echo "  J60 processed: ${j60_count}"
echo "  Summary CSV  : ${SUMMARY_CSV}"
echo "  Log file     : ${LOG_FILE}"
echo "============================================================"
