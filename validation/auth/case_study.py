# case_study.py
# 16 March 2025

import time

from z3 import *

from src.solvers.auth_solver import AuthorizationConsistencySolver

from validation.common.output_utils import logConstraints, logResults
from validation.common.parse_args import readCommandLineArgs

if __name__ == "__main__":
    msSystem, DEBUG = readCommandLineArgs(sys.argv)

    print("Performing tests...")
    s = AuthorizationConsistencySolver(msSystem)

    start_time = time.perf_counter()

    s.addAtLeastOnePermittedRoleConstraints()
    s.addEndpointPermittedRoleConstraints()
    s.addDataEntityOperationConsistencyConstraints()

    print("Is system satisfiable?")
    sol = s.buildVerifier()
    print(sol.check())

    print("Applying optimizer...")
    opt = s.buildOptimizer()
    model = None
    print(opt.check())
    if opt.check() == sat:
        model = opt.model()

    end_time = time.perf_counter()

    print(f"Completed constraint generation and solving in {end_time-start_time} seconds.\n")

    if model is not None:
        print("Logging full optimizer results to data/results.txt...")
        print("Outputting solver suggestions...")
        logResults(model, msSystem)

    if DEBUG is True:
        print("Logging constraints to constraints.txt...")
        logConstraints(sol)
