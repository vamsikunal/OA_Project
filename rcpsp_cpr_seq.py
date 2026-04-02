"""
MILP implementation of the novel SEQ model for RCPSP-CPR from:
Klein, Gnägi, Trautmann - "Mixed-integer linear programming for project scheduling under various resource constraints"

This implements the fully extended continuous-time model (SEQ_EF/SEQ) using Gurobi.

Model components:
- Variables: S_i (start times), y_ij (completion-start sequencing), z_ij (start-start sequencing)
- Constraints: (2)-(6) for base model, (7)-(12) for valid inequalities
- Objective: Minimize makespan (start time of sink activity)
"""

import gurobipy as gp
from gurobipy import GRB
import pathlib


class RCPSPCPRSolver:
    """
    Solver for the Resource-Constrained Project Scheduling Problem with 
    Consumption and Production of resources (RCPSP-CPR) using the novel 
    SEQ MILP model.
    """
    
    def __init__(self, instance_file=None):
        self.instance_file = instance_file
        self.model = None
        self.solution = None
        
        # Problem data
        self.n = 0              # Number of real activities (excl. dummies)
        self.V = []             # Set of all activities {0, 1, ..., n+1}
        self.E = []             # Precedence relations
        self.TE = set()         # Transitive closure of E
        self.R = []             # Set of renewable resources
        self.C = []             # Set of storage resources
        
        # Parameters
        self.p = {}             # Duration p_i for each activity
        self.r = {}             # Renewable resource demand r_ik
        self.c_minus = {}       # Storage resource consumption c_ik^-
        self.c_plus = {}        # Storage resource production c_ik^+
        self.R_cap = {}         # Renewable resource capacity R_k
        self.C_cap = {}         # Storage resource initial stock C_k
        
        # Scheduling horizon (upper bound on makespan)
        self.T_horizon = 0
        
        # Decision variables
        self.S = None           # Start times
        self.y = None           # Completion-start sequencing variables
        self.z = None           # Start-start sequencing variables
        
    def parse_psplib(self, file_path, include_storage=False):
        """
        Parse PSPLIB format instance file.
        
        Parameters:
        -----------
        file_path : str or Path
            Path to the .sm instance file
        include_storage : bool
            If True, parse storage resource data (for CPR instances)
        """
        file_path = pathlib.Path(file_path)
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Parse basic info
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

        # FIX #6: track whether we've already consumed the header row in each section
        requests_header_skipped = False
        availability_header_skipped = False
        
        num_renewable = 0
        num_nonrenewable = 0
        num_doubly = 0
        
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            if 'PRECEDENCE RELATIONS' in line:
                in_precedence = True
                in_requests = False
                in_resources = False
                in_availability = False
                continue
            elif 'REQUESTS/DURATIONS' in line:
                in_precedence = False
                in_requests = True
                in_resources = False
                in_availability = False
                requests_header_skipped = False   # reset for this section
                continue
            elif 'RESOURCEAVAILABILITIES' in line:
                in_precedence = False
                in_requests = False
                in_resources = False
                in_availability = True
                availability_header_skipped = False  # reset for this section
                continue
            elif 'RESOURCES' in line:
                in_resources = True
                in_precedence = False
                in_requests = False
                in_availability = False
                continue
            
            # Skip empty lines and comments
            if not line or line.startswith('*'):
                continue
            
            # Parse resource counts (RESOURCES section has format: "  - renewable : 4 R")
            if in_resources:
                if 'renewable' in line.lower() and 'nonrenewable' not in line.lower() and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        num_part = parts[1].strip().split()[0]
                        try:
                            num_renewable = int(num_part)
                        except ValueError:
                            pass
                elif 'nonrenewable' in line.lower() and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        num_part = parts[1].strip().split()[0]
                        try:
                            num_nonrenewable = int(num_part)
                        except ValueError:
                            pass
                elif 'doubly constrained' in line.lower() and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        num_part = parts[1].strip().split()[0]
                        try:
                            num_doubly = int(num_part)
                        except ValueError:
                            pass
                elif 'PROJECT INFORMATION' in line or 'PRECEDENCE' in line or 'REQUESTS' in line or 'RESOURCEAVAILABILITIES' in line:
                    in_resources = False
                continue
            
            # Parse precedence relations
            if in_precedence:
                parts = line.split()
                # FIX #6: skip the "jobnr. #modes #successors successors" header row explicitly
                if parts[0].lower().startswith('jobnr'):
                    continue
                if len(parts) >= 4 and parts[0].isdigit():
                    job = int(parts[0])
                    num_successors = int(parts[2])
                    if num_successors > 0 and len(parts) >= 3 + num_successors:
                        successors = [int(s) for s in parts[3:3+num_successors]]
                        for succ in successors:
                            self.E.append((job, succ))
                continue
            
            # Parse requests/durations
            if in_requests:
                parts = line.split()
                # FIX #6: skip the column-header row ("jobnr. mode duration  R 1  R 2 ...")
                if not requests_header_skipped:
                    requests_header_skipped = True
                    continue
                if len(parts) >= 4 and parts[0].isdigit():
                    job = int(parts[0])
                    # mode = int(parts[1])  # single-mode instances; ignored
                    duration = int(parts[2])
                    demands = [int(d) for d in parts[3:3+num_renewable+num_nonrenewable+num_doubly]]
                    
                    self.p[job] = duration
                    for k, demand in enumerate(demands):
                        self.r[(job, k)] = demand
            
            # Parse resource availabilities
            if in_availability:
                parts = line.split()
                # FIX #6: skip the "R 1  R 2 ..." header row
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
        
        # Set up activity set V = {0, 1, ..., n+1}
        # In PSPLIB, activities are 1-indexed, with 1 as source and n as sink
        self.V = list(range(1, max(self.p.keys()) + 1))
        
        # Set up resource sets
        self.R = list(range(num_renewable))
        self.C = list(range(num_renewable, num_renewable + num_nonrenewable + num_doubly))
        
        # Compute transitive closure of precedence relations
        self._compute_transitive_closure()
        
        # Compute scheduling horizon (sum of all durations = crude upper bound on makespan)
        self.T_horizon = sum(self.p[i] for i in self.V)
        
        # For CPR instances, storage resource data requires extended PSPLIB format.
        # Initialise with zeros; override externally when CPR data is available.
        for i in self.V:
            for k in self.C:
                self.c_minus[(i, k)] = 0
                self.c_plus[(i, k)] = 0

        # -----------------------------------------------------------------------
        # FIX #7: validate parsed data
        # -----------------------------------------------------------------------
        source = min(self.V)
        sink   = max(self.V)

        assert self.p[source] == 0, (
            f"Source activity {source} must have duration 0, got {self.p[source]}"
        )
        assert self.p[sink] == 0, (
            f"Sink activity {sink} must have duration 0, got {self.p[sink]}"
        )
        assert len(self.R_cap) == num_renewable, (
            f"Expected {num_renewable} resource capacities, parsed {len(self.R_cap)}"
        )
        for i in self.V:
            assert i in self.p, f"Activity {i} has no duration entry"
            for k in self.R:
                assert (i, k) in self.r, f"Activity {i} missing renewable demand for resource {k}"
        # Check DAG (no self-loops and no (i,j) and (j,i) both in TE)
        for (i, j) in self.TE:
            assert (j, i) not in self.TE, (
                f"Cycle detected in precedence graph between {i} and {j}"
            )
        # -----------------------------------------------------------------------
        
        print(f"[PARSE] Activities: {len(self.V)} (real: {len(self.V) - 2})")
        print(f"[PARSE] Renewable resources: {len(self.R)}")
        print(f"[PARSE] Storage resources: {len(self.C)}")
        print(f"[PARSE] Precedence relations: {len(self.E)}")
        print(f"[PARSE] Resource capacities: {self.R_cap}")
        print(f"[PARSE] Scheduling horizon: {self.T_horizon}")
        
    def _compute_transitive_closure(self):
        """Compute transitive closure of precedence relations using Floyd-Warshall."""
        n_max = max(self.V) + 1
        reach = [[False] * n_max for _ in range(n_max)]
        
        for (i, j) in self.E:
            reach[i][j] = True
        
        # Floyd-Warshall
        for k in self.V:
            for i in self.V:
                for j in self.V:
                    if reach[i][k] and reach[k][j]:
                        reach[i][j] = True
        
        self.TE = set()
        for i in self.V:
            for j in self.V:
                if i != j and reach[i][j]:
                    self.TE.add((i, j))
    
    def build_model(self, model_type='SEQ', time_limit=500):
        """
        Build the MILP model.
        
        Parameters:
        -----------
        model_type : str
            'SEQ_NE' - No extensions (constraints 2-6 only)
            'SEQ_EL' - Extended with inequalities (7)-(9)
            'SEQ_EF' - Fully extended with inequalities (7)-(12)
            'SEQ'    - Same as SEQ_EF but with integer start times
        time_limit : int
            Solver time limit in seconds (FIX #8: was hardcoded, now a parameter)
        """
        self.model = gp.Model("RCPSP_CPR_SEQ")
        self.model.Params.OutputFlag = 1
        self.model.Params.TimeLimit = time_limit   # FIX #8
        self.model.Params.Threads = 2
        
        V = self.V
        TE = self.TE
        R = self.R
        C = self.C
        T = self.T_horizon
        
        # =========================================================================
        # Variables
        # =========================================================================
        
        # Start time variables S_i
        if model_type == 'SEQ':
            # Integer start times (best performing configuration)
            self.S = self.model.addVars(V, vtype=GRB.INTEGER, lb=0, name="S")
        else:
            self.S = self.model.addVars(V, vtype=GRB.CONTINUOUS, lb=0, name="S")
        
        # Completion-start sequencing variables y_ij for i != j
        self.y = self.model.addVars(
            [(i, j) for i in V for j in V if i != j],
            vtype=GRB.BINARY,
            name="y"
        )
        
        # Start-start sequencing variables z_ij for pairs without transitive precedence
        z_pairs = [(i, j) for i in V for j in V 
                   if i != j and (i, j) not in TE and (j, i) not in TE]
        self.z = self.model.addVars(z_pairs, vtype=GRB.BINARY, name="z")
        
        # =========================================================================
        # Objective: Minimize makespan (start time of sink activity)
        # =========================================================================
        sink = max(V)
        self.model.setObjective(self.S[sink], GRB.MINIMIZE)
        
        # =========================================================================
        # Constraints
        # =========================================================================
        
        # FIX #2: epsilon must match the variable type.
        # For INTEGER S: epsilon = 1 is correct.
        # For CONTINUOUS S: epsilon must be 0 (the paper uses strict inequality
        # semantics captured by the big-M alone when durations are non-negative).
        epsilon = 1 if model_type == 'SEQ' else 0
        
        # Constraint (2): Link y_ij to start times
        # S_i + p_i <= S_j + T*(1 - y_ij)
        for i in V:
            for j in V:
                if i != j:
                    self.model.addConstr(
                        self.S[i] + self.p[i] <= self.S[j] + T * (1 - self.y[i, j]),
                        name=f"seq_link_{i}_{j}"
                    )
        
        # Constraint (3): Enforce precedence relations (transitive closure)
        for (i, j) in TE:
            self.model.addConstr(self.y[i, j] == 1, name=f"prec_y_{i}_{j}")
            self.model.addConstr(self.y[j, i] == 0, name=f"prec_y_rev_{i}_{j}")
        
        # Constraint (4): Link z_ij to start times (both directions)
        # z_ij = 1  iff  S_i <= S_j
        #
        # Upper link (forces z_ij = 0 when S_j < S_i):
        #   T * z_ij >= S_j - S_i + epsilon   [already present]
        # Lower link (FIX #1: forces z_ij = 0 when S_i > S_j, and prevents
        #   spuriously high z values unconstrained from below in SEQ_NE/SEQ_EL):
        #   T * z_ij <= T + S_j - S_i         i.e.  z_ij <= 1 + (S_j - S_i)/T
        #   This combined with the binary domain gives the correct semantics.
        for (i, j) in z_pairs:
            # Upper: z_ij = 1  =>  S_i <= S_j  (i starts no later than j)
            self.model.addConstr(
                T * self.z[i, j] >= self.S[j] - self.S[i] + epsilon,
                name=f"z_upper_{i}_{j}"
            )
            # Lower: S_i > S_j  =>  z_ij = 0
            self.model.addConstr(
                T * self.z[i, j] <= T + self.S[j] - self.S[i],
                name=f"z_lower_{i}_{j}"
            )
        
        # Constraint (5): Storage resource constraints
        # c_ik^- + sum_{j != i, no prec} c_jk^- * (z_ji - y_ji)
        #     <= C_k + sum_{j != i} y_ji * (c_jk^+ - c_jk^-)
        for i in V:
            for k in C:
                lhs = self.c_minus.get((i, k), 0)
                rhs = self.C_cap.get(k, 0)
                
                for j in V:
                    if j != i and (i, j) not in TE and (j, i) not in TE:
                        c_jk_minus = self.c_minus.get((j, k), 0)
                        lhs = lhs + c_jk_minus * (self.z[j, i] - self.y[j, i])
                    
                    if j != i:
                        c_jk_minus = self.c_minus.get((j, k), 0)
                        c_jk_plus  = self.c_plus.get((j, k), 0)
                        rhs = rhs + self.y[j, i] * (c_jk_plus - c_jk_minus)
                
                self.model.addConstr(lhs <= rhs, name=f"storage_{i}_{k}")
        
        # Constraint (6): Renewable resource constraints
        # r_ik + sum_{j != i, no prec} r_jk * (z_ji - y_ji) <= R_k
        #
        # FIX #3: add constraint for ALL activities, including zero-demand ones.
        # An activity with r_ik = 0 still provides a valid check that concurrent
        # in-progress activities do not exceed capacity.
        for i in V:
            for k in R:
                lhs = self.r.get((i, k), 0)
                
                for j in V:
                    if j != i and (i, j) not in TE and (j, i) not in TE:
                        r_jk = self.r.get((j, k), 0)
                        lhs = lhs + r_jk * (self.z[j, i] - self.y[j, i])
                
                self.model.addConstr(lhs <= self.R_cap[k], name=f"renewable_{i}_{k}")
        
        # =========================================================================
        # Valid inequalities
        # =========================================================================
        
        if model_type in ['SEQ_EL', 'SEQ_EF', 'SEQ']:
            # Constraint (7): Pairs that cannot be executed simultaneously
            # y_ij + y_ji >= 1 for (i,j) in F2
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
            
            # Constraint (8): Triples that cannot be executed simultaneously
            # y_ij + y_ji + y_ih + y_hi + y_jh + y_hj >= 1 for (i,j,h) in F3
            F3 = []
            for i in V:
                for j in V:
                    if i < j and (i, j) not in TE and (j, i) not in TE:
                        if (i, j) in F2:
                            continue
                        for h in V:
                            if j < h and (i, h) not in TE and (h, i) not in TE \
                                    and (j, h) not in TE and (h, j) not in TE:
                                # Skip if any sub-pair is already in F2
                                if (i, h) in F2 or (j, h) in F2:
                                    continue
                                # Add if all three together exceed some resource
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
            
            # Constraint (9): Antisymmetry of y
            # y_ij + y_ji <= 1
            for i in V:
                for j in V:
                    if i < j and (i, j) not in TE and (j, i) not in TE:
                        self.model.addConstr(
                            self.y[i, j] + self.y[j, i] <= 1,
                            name=f"antisym_{i}_{j}"
                        )
        
        if model_type in ['SEQ_EF', 'SEQ']:
            # Constraint (10): At least one starts first
            # z_ij + z_ji >= 1
            for i in V:
                for j in V:
                    if i < j and (i, j) not in TE and (j, i) not in TE:
                        self.model.addConstr(
                            self.z[i, j] + self.z[j, i] >= 1,
                            name=f"start_order_{i}_{j}"
                        )
            
            # Constraint (11): If i completes before j starts, i starts before j
            # z_ij >= y_ij
            for i in V:
                for j in V:
                    if i != j and (i, j) not in TE and (j, i) not in TE:
                        self.model.addConstr(
                            self.z[i, j] >= self.y[i, j],
                            name=f"z_ge_y_{i}_{j}"
                        )
            
            # Constraint (12): If both z_ij = z_ji = 1, then S_i = S_j
            # 2 - z_ij - z_ji >= (S_i - S_j) / T
            for i in V:
                for j in V:
                    if i != j and (i, j) not in TE and (j, i) not in TE:
                        self.model.addConstr(
                            2 - self.z[i, j] - self.z[j, i] >= (self.S[i] - self.S[j]) / T,
                            name=f"same_start_{i}_{j}"
                        )
        
        self.model.update()
        print(f"\n[MODEL] Built {model_type} model")
        print(f"[MODEL] Variables: {self.model.NumVars} (binary: {self.model.NumBinVars}, "
              f"integer: {self.model.NumIntVars})")
        print(f"[MODEL] Constraints: {self.model.NumConstrs}")
    
    def solve(self):
        """Solve the MILP model."""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        self.model.optimize()
        
        # Extract solution
        if self.model.Status in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
            self.solution = {
                'status': self.model.Status,
                'makespan': self.model.ObjVal,
                'start_times': {i: self.S[i].X for i in self.V},
                'y': {(i, j): self.y[i, j].X for i, j in self.y.keys()},
                # FIX #4: self.z is a tupledict (always truthy); check for None explicitly
                'z': {(i, j): self.z[i, j].X for i, j in self.z.keys()}
                     if self.z is not None else {},
                'mip_gap': self.model.MIPGap,
                'runtime': self.model.Runtime
            }
        else:
            self.solution = {
                'status': self.model.Status,
                'makespan': None,
                'start_times': None,
                'mip_gap': self.model.MIPGap if hasattr(self.model, 'MIPGap') else None,
                'runtime': self.model.Runtime
            }
        
        return self.solution
    
    def print_solution(self):
        """Print the solution in a readable format."""
        if self.solution is None:
            print("No solution available.")
            return
        
        print("\n" + "="*60)
        print("SOLUTION")
        print("="*60)
        
        status_names = {
            GRB.OPTIMAL:    "OPTIMAL",
            GRB.SUBOPTIMAL: "SUBOPTIMAL",
            GRB.INFEASIBLE: "INFEASIBLE",
            GRB.TIME_LIMIT: "TIME_LIMIT",
            GRB.UNBOUNDED:  "UNBOUNDED"
        }
        
        print(f"Status: {status_names.get(self.solution['status'], str(self.solution['status']))}")
        
        if self.solution['makespan'] is not None:
            print(f"Makespan: {self.solution['makespan']:.2f}")
        
        if self.solution.get('mip_gap') is not None:
            print(f"MIP Gap: {self.solution['mip_gap']*100:.4f}%")
        
        print(f"Runtime: {self.solution['runtime']:.2f} seconds")
        
        if self.solution['start_times'] is not None:
            print("\nActivity Start Times:")
            print("-"*40)
            for i in sorted(self.V):
                s = self.solution['start_times'][i]
                p = self.p.get(i, 0)
                print(f"  Activity {i:3d}: Start = {s:6.2f}, Duration = {p:3d}, "
                      f"End = {s + p:6.2f}")


def main():
    """Main function to run the solver on a PSPLIB instance."""
    import argparse
    
    parser = argparse.ArgumentParser(description='RCPSP-CPR SEQ Model Solver')
    parser.add_argument('--instance', type=str, default='j30.sm/j301_1.sm',
                        help='Path to PSPLIB instance file')
    parser.add_argument('--model', type=str, default='SEQ',
                        choices=['SEQ_NE', 'SEQ_EL', 'SEQ_EF', 'SEQ'],
                        help='Model configuration')
    parser.add_argument('--time-limit', type=int, default=500,
                        help='Time limit in seconds')
    
    args = parser.parse_args()
    
    solver = RCPSPCPRSolver(instance_file=args.instance)
    solver.parse_psplib(args.instance)
    solver.build_model(model_type=args.model, time_limit=args.time_limit)  # FIX #8
    solver.solve()
    solver.print_solution()


if __name__ == "__main__":
    main()