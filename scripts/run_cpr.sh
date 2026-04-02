#!/usr/bin/env bash
# =============================================================================
# run_cpr.sh  —  Sequential CPR experiments (RCPSP with storage resources)
#
# Synthetic c_minus / c_plus values are generated once per instance (seeded
# by instance name for reproducibility) and written to a companion JSON
# sidecar file so the same values are reused on resume.
#
# Resume-safe: already-completed instances are skipped automatically.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configurable parameters
# ---------------------------------------------------------------------------
INSTANCE_DIR="${INSTANCE_DIR:-./instances}"
RESULTS_DIR="${RESULTS_DIR:-./results}"
LOG_DIR="${LOG_DIR:-./logs}"
CPR_SEED_DIR="${CPR_SEED_DIR:-./cpr_seeds}"   # stores per-instance synthetic CPR data
PYTHON="${PYTHON:-python3}"
MODEL="${MODEL:-SEQ}"
TIME_LIMIT="${TIME_LIMIT:-500}"
J30_LIMIT="${J30_LIMIT:-240}"
J60_LIMIT="${J60_LIMIT:-120}"

# CPR generation parameters
CPR_C_MINUS_MAX="${CPR_C_MINUS_MAX:-5}"    # max consumption per activity
CPR_C_PLUS_MAX="${CPR_C_PLUS_MAX:-5}"     # max production per activity
CPR_INITIAL_STOCK="${CPR_INITIAL_STOCK:-50}"  # initial stock for each storage resource
CPR_NUM_STORAGE="${CPR_NUM_STORAGE:-2}"   # number of synthetic storage resources

RUN_ID="cpr_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_DIR}/${RUN_ID}.log"
SUMMARY_CSV="${RESULTS_DIR}/summary_cpr.csv"

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
mkdir -p "${RESULTS_DIR}/j30" "${RESULTS_DIR}/j60" "${LOG_DIR}" "${CPR_SEED_DIR}"

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "============================================================"
echo "  RCPSP CPR Experiment Run"
echo "  Run ID       : ${RUN_ID}"
echo "  Started      : $(date)"
echo "  Model        : ${MODEL}"
echo "  Limit        : J30=${J30_LIMIT}  J60=${J60_LIMIT}"
echo "  Time limit   : ${TIME_LIMIT}s per instance"
echo "  Storage res  : ${CPR_NUM_STORAGE}"
echo "  c_minus max  : ${CPR_C_MINUS_MAX}"
echo "  c_plus  max  : ${CPR_C_PLUS_MAX}"
echo "  Init. stock  : ${CPR_INITIAL_STOCK}"
echo "============================================================"

if [[ ! -f "${SUMMARY_CSV}" ]]; then
    echo "run_id,instance,set,status,makespan,runtime_s,mip_gap,num_storage,timestamp" \
        > "${SUMMARY_CSV}"
fi

# ---------------------------------------------------------------------------
# Helper: generate (or load cached) synthetic CPR seed for an instance
# Returns path to the seed JSON file.
# ---------------------------------------------------------------------------
ensure_cpr_seed() {
    local instance_path="$1"
    local instance_name
    instance_name="$(basename "${instance_path}" .sm)"
    local seed_file="${CPR_SEED_DIR}/${instance_name}_cpr_seed.json"

    if [[ -s "${seed_file}" ]]; then
        echo "${seed_file}"
        return 0
    fi

    # Generate seed deterministically from instance name (reproducible)
    "${PYTHON}" - <<PYEOF
import json, hashlib, random, pathlib

instance_path = "${instance_path}"
seed_file     = "${seed_file}"
num_storage   = ${CPR_NUM_STORAGE}
c_minus_max   = ${CPR_C_MINUS_MAX}
c_plus_max    = ${CPR_C_PLUS_MAX}
initial_stock = ${CPR_INITIAL_STOCK}

# Deterministic seed from instance name
name = pathlib.Path(instance_path).stem
seed = int(hashlib.sha256(name.encode()).hexdigest(), 16) % (2**32)
rng  = random.Random(seed)

# Parse activity count from file (needed to generate per-activity values)
num_activities = 0
with open(instance_path) as f:
    for line in f:
        if 'jobs (incl. supersource/sink)' in line or 'jobs' in line.lower():
            parts = line.split(':')
            if len(parts) == 2:
                try:
                    num_activities = int(parts[1].strip().split()[0])
                    break
                except ValueError:
                    pass

# Fallback: count activity lines in REQUESTS/DURATIONS section
if num_activities == 0:
    in_req = False
    with open(instance_path) as f:
        for line in f:
            if 'REQUESTS/DURATIONS' in line:
                in_req = True
                continue
            if in_req:
                parts = line.split()
                if len(parts) >= 3 and parts[0].isdigit():
                    num_activities = max(num_activities, int(parts[0]))
                elif '***' in line:
                    break

activities = list(range(1, num_activities + 1))
c_minus = {}
c_plus  = {}

for k in range(num_storage):
    for i in activities:
        # Source and sink dummies consume/produce nothing
        if i == 1 or i == num_activities:
            c_minus[str((i, k))] = 0
            c_plus[str((i, k))]  = 0
        else:
            c_minus[str((i, k))] = rng.randint(0, c_minus_max)
            c_plus[str((i, k))]  = rng.randint(0, c_plus_max)

seed_data = {
    "instance"     : name,
    "num_storage"  : num_storage,
    "initial_stock": {str(k): initial_stock for k in range(num_storage)},
    "c_minus"      : c_minus,
    "c_plus"       : c_plus,
    "rng_seed"     : seed,
}

with open(seed_file, 'w') as f:
    json.dump(seed_data, f, indent=2)

print(f"[SEED]  Generated CPR seed for {name} -> {seed_file}")
PYEOF

    echo "${seed_file}"
}

# ---------------------------------------------------------------------------
# Helper: run one CPR instance
# ---------------------------------------------------------------------------
run_instance() {
    local instance_path="$1"
    local instance_set="$2"
    local instance_name
    instance_name="$(basename "${instance_path}" .sm)"
    local result_file="${RESULTS_DIR}/${instance_set}/${instance_name}_cpr.json"

    if [[ -s "${result_file}" ]]; then
        echo "[SKIP]  ${instance_name}  (result already exists)"
        return 0
    fi

    # Ensure CPR seed exists (idempotent)
    local seed_file
    seed_file="$(ensure_cpr_seed "${instance_path}")"

    echo "[RUN]   ${instance_name}  (CPR, seed=${seed_file}) ..."
    local start_ts
    start_ts=$(date +%s)

    set +e
    "${PYTHON}" rcpsp_cpr_seq.py \
        --instance   "${instance_path}" \
        --model      "${MODEL}" \
        --time-limit "${TIME_LIMIT}" \
        --use-cpr \
        --cpr-seed   "${seed_file}" \
        --output-json "${result_file}" \
        2>&1 | tee -a "${LOG_FILE}"
    local exit_code=$?
    set -e

    local end_ts
    end_ts=$(date +%s)
    local elapsed=$(( end_ts - start_ts ))

    local status makespan runtime mip_gap
    if [[ -s "${result_file}" ]]; then
        status=$(python3   -c "import json; d=json.load(open('${result_file}')); print(d.get('status','UNKNOWN'))"  2>/dev/null || echo "PARSE_ERROR")
        makespan=$(python3 -c "import json; d=json.load(open('${result_file}')); print(d.get('makespan',''))"       2>/dev/null || echo "")
        runtime=$(python3  -c "import json; d=json.load(open('${result_file}')); print(d.get('runtime_s',''))"      2>/dev/null || echo "${elapsed}")
        mip_gap=$(python3  -c "import json; d=json.load(open('${result_file}')); print(d.get('mip_gap',''))"        2>/dev/null || echo "")
    else
        status="SOLVER_ERROR"
        makespan=""; runtime="${elapsed}"; mip_gap=""
        echo '{"status":"SOLVER_ERROR","makespan":null,"runtime_s":'"${elapsed}"',"mip_gap":null}' \
            > "${result_file}"
    fi

    echo "${RUN_ID},${instance_name},${instance_set},${status},${makespan},${runtime},${mip_gap},${CPR_NUM_STORAGE},$(date -Iseconds)" \
        >> "${SUMMARY_CSV}"

    echo "[DONE]  ${instance_name}  status=${status}  makespan=${makespan}  time=${elapsed}s"
}

# ---------------------------------------------------------------------------
# J30
# ---------------------------------------------------------------------------
echo ""
echo "--- J30 instances (CPR) ---"
j30_count=0
mapfile -t J30_FILES < <(find "${INSTANCE_DIR}/j30.sm" -name "*.sm" 2>/dev/null | sort)
j30_total=$(( ${#J30_FILES[@]} < J30_LIMIT ? ${#J30_FILES[@]} : J30_LIMIT ))

for instance in "${J30_FILES[@]}"; do
    (( j30_count >= J30_LIMIT )) && break
    j30_count=$(( j30_count + 1 ))
    echo -n "[${j30_count}/${j30_total}] "
    run_instance "${instance}" "j30"
done

# ---------------------------------------------------------------------------
# J60
# ---------------------------------------------------------------------------
echo ""
echo "--- J60 instances (CPR) ---"
j60_count=0
mapfile -t J60_FILES < <(find "${INSTANCE_DIR}/j60.sm" -name "*.sm" 2>/dev/null | sort)
j60_total=$(( ${#J60_FILES[@]} < J60_LIMIT ? ${#J60_FILES[@]} : J60_LIMIT ))

for instance in "${J60_FILES[@]}"; do
    (( j60_count >= J60_LIMIT )) && break
    j60_count=$(( j60_count + 1 ))
    echo -n "[${j60_count}/${j60_total}] "
    run_instance "${instance}" "j60"
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  CPR run complete : $(date)"
echo "  J30 processed    : ${j30_count}"
echo "  J60 processed    : ${j60_count}"
echo "  Summary CSV      : ${SUMMARY_CSV}"
echo "  Log file         : ${LOG_FILE}"
echo "============================================================"
