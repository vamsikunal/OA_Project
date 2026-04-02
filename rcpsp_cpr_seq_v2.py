"""
MILP implementation of the novel SEQ model for RCPSP-CPR from:
Klein, Gnägi, Trautmann - "Mixed-integer linear programming for project scheduling
under various resource constraints"

Supports:
  --use-cpr        : enable storage-resource (CPR) constraints
  --cpr-seed FILE  : JSON sidecar with synthetic c_minus / c_plus / initial_stock
  --output-json    : write solution to a JSON file (for batch scripting)
"""

import gurobipy as gp
from gurobipy import GRB
import pathlib
import json


class RCPSPCPRSolver:
    """
    Solver for RCPSP-CPR using the novel SEQ MILP model.
    """

    def __init__(self, instance_file=None):
        self.instance_file = instance_file
        self.model = None
        self.solution = None

        self.n = 0
        self.V = []
        self.E = []
        self.TE = set()
        self.R = []
        self.C = []

        self.p = {}
        self.r = {}
        self.c_minus = {}
        self.c_plus = {}
        self.R_cap = {}
        self.C_cap = {}

        self.T_horizon = 0

        self.S = None
        self.y = None
        self.z = None

    # =========================================================================
    # Parsing
    # =========================================================================

    def parse_psplib(self, file_path, include_storage=False):
        file_path = pathlib.Path(file_path)

        with open(file_path, 'r') as f:
            lines = f.readlines()

        self.E = []
        self.p = {}
        self.r = {}
        self.c_minus = {}
        self.c_plus = {}
        self.R_cap = {}
        self.C_cap = {}

        in_precedence = False
        in_requests = False
        in_resources = False
        in_availability = False
        requests_header_skipped = False
        availability_header_skipped = False

        num_renewable = 0
        num_nonrenewable = 0
        num_doubly = 0

        for line in lines:
            line = line.strip()

            if 'PRECEDENCE RELATIONS' in line:
                in_precedence = True; in_requests = False
                in_resources = False; in_availability = False
                continue
            elif 'REQUESTS/DURATIONS' in line:
                in_precedence = False; in_requests = True
                in_resources = False; in_availability = False
                requests_header_skipped = False
                continue
            elif 'RESOURCEAVAILABILITIES' in line:
                in_precedence = False; in_requests = False
                in_resources = False; in_availability = True
                availability_header_skipped = False
                continue
            elif 'RESOURCES' in line:
                in_resources = True; in_precedence = False
                in_requests = False; in_availability = False
                continue

            if not line or line.startswith('*'):
                continue

            if in_resources:
                if 'renewable' in line.lower() and 'nonrenewable' not in line.lower() and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        try:
                            num_renewable = int(parts[1].strip().split()[0])
                        except ValueError:
                            pass
                elif 'nonrenewable' in line.lower() and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        try:
                            num_nonrenewable = int(parts[1].strip().split()[0])
                        except ValueError:
                            pass
                elif 'doubly constrained' in line.lower() and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        try:
                            num_doubly = int(parts[1].strip().split()[0])
                        except ValueError:
                            pass
                elif any(kw in line for kw in ('PROJECT INFORMATION', 'PRECEDENCE',
                                               'REQUESTS', 'RESOURCEAVAILABILITIES')):
                    in_resources = False
                continue

            if in_precedence:
                parts = line.split()
                if parts[0].lower().startswith('jobnr'):
                    continue
                if len(parts) >= 4 and parts[0].isdigit():
                    job = int(parts[0])
                    num_successors = int(parts[2])
                    if num_successors > 0 and len(parts) >= 3 + num_successors:
                        for succ in parts[3:3 + num_successors]:
                            self.E.append((job, int(succ)))
                continue

            if in_requests:
                parts = line.split()
                if not requests_header_skipped:
                    requests_header_skipped = True
                    continue
                if len(parts) >= 4 and parts[0].isdigit():
                    job = int(parts[0])
                    duration = int(parts[2])
                    demands = [int(d) for d in
                               parts[3:3 + num_renewable + num_nonrenewable + num_doubly]]
                    self.p[job] = duration
                    for k, demand in enumerate(demands):
                        self.r[(job, k)] = demand

            if in_availability:
                parts = line.split()
                if not availability_header_skipped:
                    availability_header_skipped = True
                    continue
                caps = []
                for part in parts:
                    try:
                        caps.append(int(part))
                    except ValueError:
                        continue
                if len(caps) >= num_renewable:
                    for k, cap in enumerate(caps[:num_renewable]):
                        self.R_cap[k] = int(cap)

        self.V = list(range(1, max(self.p.keys()) + 1))
        self.R = list(range(num_renewable))
        self.C = list(range(num_renewable,
                            num_renewable + num_nonrenewable + num_doubly))

        self._compute_transitive_closure()
        self.T_horizon = sum(self.p[i] for i in self.V)

        for i in self.V:
            for k in self.C:
                self.c_minus[(i, k)] = 0
                self.c_plus[(i, k)] = 0

        # Validation
        source, sink = min(self.V), max(self.V)
        assert self.p[source] == 0, \
            f"Source {source} must have duration 0, got {self.p[source]}"
        assert self.p[sink] == 0, \
            f"Sink {sink} must have duration 0, got {self.p[sink]}"
        assert len(self.R_cap) == num_renewable, \
            f"Expected {num_renewable} capacities, got {len(self.R_cap)}"
        for i in self.V:
            assert i in self.p, f"Activity {i} missing duration"
            for k in self.R:
                assert (i, k) in self.r, \
                    f"Activity {i} missing demand for resource {k}"
        for (i, j) in self.TE:
            assert (j, i) not in self.TE, \
                f"Cycle detected between {i} and {j}"

        print(f"[PARSE] Activities : {len(self.V)} (real: {len(self.V) - 2})")
        print(f"[PARSE] Renewable  : {len(self.R)}")
        print(f"[PARSE] Storage    : {len(self.C)}")
        print(f"[PARSE] Precedences: {len(self.E)}")
        print(f"[PARSE] Capacities : {self.R_cap}")
        print(f"[PARSE] Horizon    : {self.T_horizon}")

    def load_cpr_seed(self, seed_file):
        """
        Load synthetic CPR data from a JSON seed file produced by run_cpr.sh.
        Adds synthetic storage resources to the instance.
        """
        seed_file = pathlib.Path(seed_file)
        with open(seed_file, 'r') as f:
            seed = json.load(f)

        num_storage = seed['num_storage']
        # Storage resource indices start after renewable resources
        base = len(self.R)
        storage_indices = list(range(base, base + num_storage))
        self.C = storage_indices

        for k_local, k_global in enumerate(storage_indices):
            self.C_cap[k_global] = seed['initial_stock'][str(k_local)]

        for i in self.V:
            for k_local, k_global in enumerate(storage_indices):
                key_str = str((i, k_local))
                self.c_minus[(i, k_global)] = seed['c_minus'].get(key_str, 0)
                self.c_plus[(i, k_global)]  = seed['c_plus'].get(key_str, 0)

        print(f"[CPR]   Loaded seed: {seed_file.name}")
        print(f"[CPR]   Storage resources added : {num_storage}")
        print(f"[CPR]   Initial stock           : {seed['initial_stock']}")

    # =========================================================================
    # Transitive closure
    # =========================================================================

    def _compute_transitive_closure(self):
        n_max = max(self.V) + 1
        reach = [[False] * n_max for _ in range(n_max)]
        for (i, j) in self.E:
            reach[i][j] = True
        for k in self.V:
            for i in self.V:
                for j in self.V:
                    if reach[i][k] and reach[k][j]:
                        reach[i][j] = True
        self.TE = {(i, j) for i in self.V for j in self.V if i != j and reach[i][j]}

    # =========================================================================
    # Model building
    # =========================================================================

    def build_model(self, model_type='SEQ', time_limit=500):
        self.model = gp.Model("RCPSP_CPR_SEQ")
        self.model.Params.OutputFlag = 1
        self.model.Params.TimeLimit = time_limit
        self.model.Params.Threads = 2

        V = self.V
        TE = self.TE
        R = self.R
        C = self.C
        T = self.T_horizon

        # ----- Variables -----------------------------------------------------
        if model_type == 'SEQ':
            self.S = self.model.addVars(V, vtype=GRB.INTEGER, lb=0, name="S")
        else:
            self.S = self.model.addVars(V, vtype=GRB.CONTINUOUS, lb=0, name="S")

        self.y = self.model.addVars(
            [(i, j) for i in V for j in V if i != j],
            vtype=GRB.BINARY, name="y"
        )

        z_pairs = [(i, j) for i in V for j in V
                   if i != j and (i, j) not in TE and (j, i) not in TE]
        self.z = self.model.addVars(z_pairs, vtype=GRB.BINARY, name="z")

        # ----- Objective -----------------------------------------------------
        sink = max(V)
        self.model.setObjective(self.S[sink], GRB.MINIMIZE)

        # ----- epsilon (FIX #2) ----------------------------------------------
        epsilon = 1 if model_type == 'SEQ' else 0

        # Constraint (2): S_i + p_i <= S_j + T*(1 - y_ij)
        for i in V:
            for j in V:
                if i != j:
                    self.model.addConstr(
                        self.S[i] + self.p[i] <= self.S[j] + T * (1 - self.y[i, j]),
                        name=f"seq_link_{i}_{j}"
                    )

        # Constraint (3): enforce transitive precedence
        for (i, j) in TE:
            self.model.addConstr(self.y[i, j] == 1, name=f"prec_y_{i}_{j}")
            self.model.addConstr(self.y[j, i] == 0, name=f"prec_y_rev_{i}_{j}")

        # Constraint (4): link z_ij to start times — both bounds (FIX #1)
        for (i, j) in z_pairs:
            self.model.addConstr(
                T * self.z[i, j] >= self.S[j] - self.S[i] + epsilon,
                name=f"z_upper_{i}_{j}"
            )
            self.model.addConstr(
                T * self.z[i, j] <= T + self.S[j] - self.S[i],
                name=f"z_lower_{i}_{j}"
            )

        # Constraint (5): storage resource constraints
        for i in V:
            for k in C:
                lhs = self.c_minus.get((i, k), 0)
                rhs = self.C_cap.get(k, 0)
                for j in V:
                    if j != i and (i, j) not in TE and (j, i) not in TE:
                        lhs = lhs + self.c_minus.get((j, k), 0) * (self.z[j, i] - self.y[j, i])
                    if j != i:
                        rhs = rhs + self.y[j, i] * (
                            self.c_plus.get((j, k), 0) - self.c_minus.get((j, k), 0)
                        )
                self.model.addConstr(lhs <= rhs, name=f"storage_{i}_{k}")

        # Constraint (6): renewable resource constraints — all activities (FIX #3)
        for i in V:
            for k in R:
                lhs = self.r.get((i, k), 0)
                for j in V:
                    if j != i and (i, j) not in TE and (j, i) not in TE:
                        lhs = lhs + self.r.get((j, k), 0) * (self.z[j, i] - self.y[j, i])
                self.model.addConstr(lhs <= self.R_cap[k], name=f"renewable_{i}_{k}")

        # ----- Valid inequalities --------------------------------------------
        if model_type in ('SEQ_EL', 'SEQ_EF', 'SEQ'):
            F2 = set()
            for i in V:
                for j in V:
                    if i < j and (i, j) not in TE and (j, i) not in TE:
                        for k in R:
                            if self.r.get((i, k), 0) + self.r.get((j, k), 0) > self.R_cap[k]:
                                F2.add((i, j))
                                break
            for (i, j) in F2:
                self.model.addConstr(
                    self.y[i, j] + self.y[j, i] >= 1,
                    name=f"conflict2_{i}_{j}"
                )

            F3 = []
            for i in V:
                for j in V:
                    if i < j and (i, j) not in TE and (j, i) not in TE and (i, j) not in F2:
                        for h in V:
                            if j < h \
                                    and (i, h) not in TE and (h, i) not in TE \
                                    and (j, h) not in TE and (h, j) not in TE \
                                    and (i, h) not in F2 and (j, h) not in F2:
                                for k in R:
                                    if (self.r.get((i, k), 0) +
                                            self.r.get((j, k), 0) +
                                            self.r.get((h, k), 0) > self.R_cap[k]):
                                        F3.append((i, j, h))
                                        break
            for (i, j, h) in F3:
                self.model.addConstr(
                    self.y[i, j] + self.y[j, i] +
                    self.y[i, h] + self.y[h, i] +
                    self.y[j, h] + self.y[h, j] >= 1,
                    name=f"conflict3_{i}_{j}_{h}"
                )

            for i in V:
                for j in V:
                    if i < j and (i, j) not in TE and (j, i) not in TE:
                        self.model.addConstr(
                            self.y[i, j] + self.y[j, i] <= 1,
                            name=f"antisym_{i}_{j}"
                        )

        if model_type in ('SEQ_EF', 'SEQ'):
            for i in V:
                for j in V:
                    if i < j and (i, j) not in TE and (j, i) not in TE:
                        self.model.addConstr(
                            self.z[i, j] + self.z[j, i] >= 1,
                            name=f"start_order_{i}_{j}"
                        )
            for i in V:
                for j in V:
                    if i != j and (i, j) not in TE and (j, i) not in TE:
                        self.model.addConstr(
                            self.z[i, j] >= self.y[i, j],
                            name=f"z_ge_y_{i}_{j}"
                        )
            for i in V:
                for j in V:
                    if i != j and (i, j) not in TE and (j, i) not in TE:
                        self.model.addConstr(
                            2 - self.z[i, j] - self.z[j, i] >= (self.S[i] - self.S[j]) / T,
                            name=f"same_start_{i}_{j}"
                        )

        self.model.update()
        print(f"\n[MODEL] Built {model_type} model")
        print(f"[MODEL] Variables   : {self.model.NumVars} "
              f"(binary={self.model.NumBinVars}, integer={self.model.NumIntVars})")
        print(f"[MODEL] Constraints : {self.model.NumConstrs}")

    # =========================================================================
    # Solve
    # =========================================================================

    def solve(self):
        if self.model is None:
            raise ValueError("Call build_model() first.")
        self.model.optimize()

        if self.model.Status in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
            self.solution = {
                'status':      'OPTIMAL' if self.model.Status == GRB.OPTIMAL else 'SUBOPTIMAL',
                'makespan':    self.model.ObjVal,
                'runtime_s':   self.model.Runtime,
                'mip_gap':     self.model.MIPGap,
                'start_times': {i: self.S[i].X for i in self.V},
                'y': {f"{i},{j}": self.y[i, j].X for i, j in self.y.keys()},
                'z': {f"{i},{j}": self.z[i, j].X for i, j in self.z.keys()}
                     if self.z is not None else {},   # FIX #4
            }
        else:
            status_map = {
                GRB.INFEASIBLE: 'INFEASIBLE',
                GRB.TIME_LIMIT: 'TIME_LIMIT',
                GRB.UNBOUNDED:  'UNBOUNDED',
            }
            self.solution = {
                'status':    status_map.get(self.model.Status, str(self.model.Status)),
                'makespan':  None,
                'runtime_s': self.model.Runtime,
                'mip_gap':   self.model.MIPGap if hasattr(self.model, 'MIPGap') else None,
                'start_times': None,
            }
        return self.solution

    def write_json(self, output_path):
        """Write solution dict to a JSON file (used by batch scripts)."""
        output_path = pathlib.Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.solution, f, indent=2)
        print(f"[OUT]   Solution written to {output_path}")

    def print_solution(self):
        if self.solution is None:
            print("No solution available.")
            return
        print("\n" + "=" * 60)
        print("SOLUTION")
        print("=" * 60)
        print(f"Status  : {self.solution['status']}")
        if self.solution['makespan'] is not None:
            print(f"Makespan: {self.solution['makespan']:.2f}")
        if self.solution.get('mip_gap') is not None:
            print(f"MIP Gap : {self.solution['mip_gap'] * 100:.4f}%")
        print(f"Runtime : {self.solution['runtime_s']:.2f}s")
        if self.solution.get('start_times'):
            print("\nActivity Start Times:")
            print("-" * 40)
            for i in sorted(self.V):
                s = self.solution['start_times'][i]
                p = self.p.get(i, 0)
                print(f"  Activity {i:3d}: Start={s:6.2f}  Dur={p:3d}  End={s + p:6.2f}")


# =============================================================================
# CLI entry point
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='RCPSP-CPR SEQ Model Solver')
    parser.add_argument('--instance',    type=str, default='j30.sm/j301_1.sm')
    parser.add_argument('--model',       type=str, default='SEQ',
                        choices=['SEQ_NE', 'SEQ_EL', 'SEQ_EF', 'SEQ'])
    parser.add_argument('--time-limit',  type=int, default=500)
    parser.add_argument('--use-cpr',     action='store_true',
                        help='Enable CPR (storage resource) constraints')
    parser.add_argument('--cpr-seed',    type=str, default=None,
                        help='Path to JSON sidecar with synthetic CPR data')
    parser.add_argument('--output-json', type=str, default=None,
                        help='Write solution to this JSON file')
    args = parser.parse_args()

    solver = RCPSPCPRSolver(instance_file=args.instance)
    solver.parse_psplib(args.instance)

    if args.use_cpr:
        if args.cpr_seed is None:
            parser.error('--use-cpr requires --cpr-seed <seed_file.json>')
        solver.load_cpr_seed(args.cpr_seed)

    solver.build_model(model_type=args.model, time_limit=args.time_limit)
    solver.solve()
    solver.print_solution()

    if args.output_json:
        solver.write_json(args.output_json)


if __name__ == "__main__":
    main()
