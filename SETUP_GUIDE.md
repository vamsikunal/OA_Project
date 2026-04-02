# Experiment Pipeline — VM & GCS Setup Guide

## Overview

| VM   | Role              | Instances           |
|------|-------------------|---------------------|
| VM-1 | Non-CPR (standard RCPSP) | J30 × 240, J60 × 120 |
| VM-2 | CPR (storage resources)  | J30 × 240, J60 × 120 |

Both VMs sync results continuously to a shared GCS bucket so that data
survives spot-instance preemption.

---

## Part 1 — GCS Bucket Setup

### 1.1 Create the bucket

```bash
# Choose a globally unique name
export BUCKET="rcpsp-results-$(whoami)-$(date +%Y%m)"

gcloud storage buckets create "gs://${BUCKET}" \
    --location=us-central1 \
    --uniform-bucket-level-access

echo "Bucket: gs://${BUCKET}"
```

### 1.2 Set lifecycle rule (optional — auto-delete after 90 days)

```bash
cat > /tmp/lifecycle.json <<'EOF'
{
  "rule": [{
    "action": {"type": "Delete"},
    "condition": {"age": 90}
  }]
}
EOF

gsutil lifecycle set /tmp/lifecycle.json "gs://${BUCKET}"
```

### 1.3 Pre-create result folders (optional but tidy)

```bash
for dir in results/j30 results/j60 logs cpr_seeds; do
    gsutil cp /dev/null "gs://${BUCKET}/${dir}/.keep"
done
```

---

## Part 2 — VM Creation

### 2.1 Non-CPR VM (VM-1)

```bash
gcloud compute instances create rcpsp-vm-non-cpr \
    --zone=us-central1-a \
    --machine-type=n2-standard-4 \
    --boot-disk-size=100GB \
    --boot-disk-type=pd-ssd \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --scopes=storage-rw \
    --metadata=startup-script='#! /bin/bash
        apt-get update -y
        apt-get install -y python3-pip git curl'
```

### 2.2 CPR VM (VM-2)

```bash
gcloud compute instances create rcpsp-vm-cpr \
    --zone=us-central1-b \
    --machine-type=n2-standard-4 \
    --boot-disk-size=100GB \
    --boot-disk-type=pd-ssd \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --scopes=storage-rw \
    --metadata=startup-script='#! /bin/bash
        apt-get update -y
        apt-get install -y python3-pip git curl'
```

> **Spot instances**: add `--provisioning-model=SPOT --instance-termination-action=STOP`
> to reduce cost. The sync daemon and resume-safe scripts handle preemption gracefully.

---

## Part 3 — VM Dependencies (run on each VM)

### 3.1 SSH into the VM

```bash
# VM-1
gcloud compute ssh rcpsp-vm-non-cpr --zone=us-central1-a

# VM-2
gcloud compute ssh rcpsp-vm-cpr --zone=us-central1-b
```

### 3.2 Install Python dependencies

```bash
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git curl wget

python3 -m venv ~/venv
source ~/venv/bin/activate

pip install --upgrade pip
pip install gurobipy          # Gurobi Python bindings
```

### 3.3 Install Gurobi

```bash
cd /opt
sudo wget https://packages.gurobi.com/11.0/gurobi11.0.3_linux64.tar.gz
sudo tar xzf gurobi11.0.3_linux64.tar.gz
sudo ln -sf /opt/gurobi1103/linux64 /opt/gurobi

# Add to environment (append to ~/.bashrc)
cat >> ~/.bashrc <<'EOF'
export GUROBI_HOME=/opt/gurobi
export PATH="${GUROBI_HOME}/bin:${PATH}"
export LD_LIBRARY_PATH="${GUROBI_HOME}/lib:${LD_LIBRARY_PATH}"
EOF

source ~/.bashrc
```

### 3.4 Activate Gurobi licence

```bash
# Cloud/WLS licence — set the key as an environment variable
export GRB_LICENSE_FILE=/opt/gurobi/gurobi.lic   # or wherever your .lic file lives

# If using a token server:
# echo "TOKENSERVER=<server-ip>" > /opt/gurobi/gurobi.lic
# echo "PORT=41954"             >> /opt/gurobi/gurobi.lic

# Test
gurobi_cl --version
```

### 3.5 Install gcloud CLI (if not pre-installed)

```bash
curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts
exec -l $SHELL
gcloud init          # follow the prompts — select project and region
gcloud auth application-default login   # gives gsutil credentials
```

---

## Part 4 — Clone Repository & Configure

```bash
source ~/venv/bin/activate

git clone https://github.com/<your-org>/<your-repo>.git ~/rcpsp
cd ~/rcpsp

# Make scripts executable
chmod +x scripts/run_non_cpr.sh scripts/run_cpr.sh scripts/sync_to_gcs.sh
```

### 4.1 Set shared environment variables

Create a `.env` file (sourced by the scripts):

```bash
cat > ~/rcpsp/.env <<EOF
export INSTANCE_DIR="\${HOME}/rcpsp/instances"
export RESULTS_DIR="\${HOME}/rcpsp/results"
export LOG_DIR="\${HOME}/rcpsp/logs"
export CPR_SEED_DIR="\${HOME}/rcpsp/cpr_seeds"
export PYTHON="\${HOME}/venv/bin/python3"
export GCS_BUCKET="gs://${BUCKET}"        # set BUCKET before running this
export MODEL="SEQ"
export TIME_LIMIT="500"
export J30_LIMIT="240"
export J60_LIMIT="120"
export GRB_LICENSE_FILE="/opt/gurobi/gurobi.lic"
EOF

source ~/rcpsp/.env
```

### 4.2 Download PSPLIB instances

```bash
mkdir -p ~/rcpsp/instances
cd ~/rcpsp/instances

# J30 (480 instances)
wget -q http://www.om-db.wi.tum.de/psplib/files/j30.sm.tgz
tar xzf j30.sm.tgz

# J60 (480 instances)
wget -q http://www.om-db.wi.tum.de/psplib/files/j60.sm.tgz
tar xzf j60.sm.tgz

ls j30.sm/ | wc -l   # should show 480
ls j60.sm/ | wc -l   # should show 480
```

---

## Part 5 — Running Experiments

### 5.1 Start the GCS sync daemon (both VMs)

```bash
cd ~/rcpsp
source .env

# Start sync daemon in background; log PID for later
nohup bash scripts/sync_to_gcs.sh > logs/sync_daemon.out 2>&1 &
echo $! > logs/sync_daemon.pid
echo "Sync daemon PID: $(cat logs/sync_daemon.pid)"
```

### 5.2 VM-1: Non-CPR experiments

```bash
cd ~/rcpsp
source .env

nohup bash scripts/run_non_cpr.sh > logs/run_non_cpr_main.out 2>&1 &
echo $! > logs/run_non_cpr.pid
echo "Non-CPR runner PID: $(cat logs/run_non_cpr.pid)"

# Tail live progress
tail -f logs/run_non_cpr_main.out
```

### 5.3 VM-2: CPR experiments

```bash
cd ~/rcpsp
source .env

nohup bash scripts/run_cpr.sh > logs/run_cpr_main.out 2>&1 &
echo $! > logs/run_cpr.pid
echo "CPR runner PID: $(cat logs/run_cpr.pid)"

tail -f logs/run_cpr_main.out
```

### 5.4 Resume after preemption

Because results are written to individual JSON files and already-complete
instances are skipped, simply re-run the same command:

```bash
# On VM-1
cd ~/rcpsp && source .env
nohup bash scripts/run_non_cpr.sh >> logs/run_non_cpr_main.out 2>&1 &

# On VM-2
cd ~/rcpsp && source .env
nohup bash scripts/run_cpr.sh >> logs/run_cpr_main.out 2>&1 &
```

---

## Part 6 — Monitoring & Retrieving Results

### 6.1 Check progress from local log

```bash
# Count completed results
ls results/j30/*_non_cpr.json 2>/dev/null | wc -l
ls results/j60/*_non_cpr.json 2>/dev/null | wc -l

# Tail the latest log
tail -f logs/non_cpr_*.log | grep -E '\[RUN\]|\[DONE\]|\[SKIP\]'
```

### 6.2 Check what's in GCS

```bash
gsutil ls -l "gs://${BUCKET}/results/j30/" | tail -5
gsutil ls -l "gs://${BUCKET}/results/j60/" | tail -5
```

### 6.3 Download results locally (from your workstation)

```bash
mkdir -p ~/rcpsp_results
gsutil -m rsync -r "gs://${BUCKET}/results" ~/rcpsp_results/
```

### 6.4 Quick summary from CSV

```bash
# Count by status
awk -F',' 'NR>1 {print $4}' results/summary_non_cpr.csv | sort | uniq -c
awk -F',' 'NR>1 {print $4}' results/summary_cpr.csv     | sort | uniq -c

# Average makespan for OPTIMAL runs
python3 - <<'EOF'
import csv, statistics
with open('results/summary_non_cpr.csv') as f:
    rows = [r for r in csv.DictReader(f) if r['status'] == 'OPTIMAL']
spans = [float(r['makespan']) for r in rows if r['makespan']]
print(f"Non-CPR  OPTIMAL: {len(rows)}  avg makespan: {statistics.mean(spans):.1f}")
EOF
```

---

## Part 7 — Folder Structure

```
~/rcpsp/
├── rcpsp_cpr_seq.py          # solver (updated with --use-cpr / --cpr-seed / --output-json)
├── .env                      # environment variables
├── instances/
│   ├── j30.sm/               # 480 J30 PSPLIB instances
│   └── j60.sm/               # 480 J60 PSPLIB instances
├── scripts/
│   ├── run_non_cpr.sh        # VM-1 experiment runner
│   ├── run_cpr.sh            # VM-2 experiment runner
│   └── sync_to_gcs.sh        # background GCS sync daemon
├── results/
│   ├── j30/
│   │   ├── j301_1_non_cpr.json
│   │   ├── j301_1_cpr.json
│   │   └── ...
│   ├── j60/
│   │   └── ...
│   ├── summary_non_cpr.csv   # per-run summary (non-CPR)
│   └── summary_cpr.csv       # per-run summary (CPR)
├── cpr_seeds/
│   ├── j301_1_cpr_seed.json  # deterministic synthetic CPR data per instance
│   └── ...
└── logs/
    ├── non_cpr_<timestamp>.log
    ├── cpr_<timestamp>.log
    └── sync_<timestamp>.log
```

---

## Part 8 — Cleanup

```bash
# Stop sync daemon
kill "$(cat logs/sync_daemon.pid)" 2>/dev/null

# Delete VMs when done
gcloud compute instances delete rcpsp-vm-non-cpr --zone=us-central1-a --quiet
gcloud compute instances delete rcpsp-vm-cpr     --zone=us-central1-b --quiet

# (Optional) delete bucket
# gsutil rm -r "gs://${BUCKET}"
```
