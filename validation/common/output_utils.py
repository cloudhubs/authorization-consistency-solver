# output_utils.py
# 16 June 2025

from src.solvers.auth_solver import AuthorizationConsistencySolver
from src.ms_system import MicroserviceSystem

from z3 import ModelRef, Solver

def logConstraints(sol: Solver):
    with open("data/constraints.txt", "w") as f:
        for c in sol.assertions():
            f.write(str(c) + "\n")


def logResults(model: ModelRef, msSystem: MicroserviceSystem):
    count = 0
    with open("data/results.txt", "w") as f:
        print("\nSUGGESTIONS:")
        for r in model.decls():
            temp = r.name()
            temp = temp.replace("_permittedRoles", "")
            if (model[r].as_long() != msSystem.findEndpoint(temp).allowedRoles):
                count += 1
                f.write("DIFFERENT: ")
                print(f"{r.name()} = {model[r]}")
            f.write(f"{r.name()} = {model[r]}\n")
    print("\nNumber of changes suggested by the solver: " + str(count))