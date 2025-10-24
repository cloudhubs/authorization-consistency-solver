# tests.py
# 7 March 2025

from z3 import *

from src.solvers.auth_solver import AuthorizationConsistencySolver
from validation.common.test_system import getTestMicroserviceSystem

if __name__ == "__main__":
    def prepareTest(test):
        # Print test number
        print(f"TEST {test}")

        # Prepare microservice system
        msSystem = getTestMicroserviceSystem()

        # Prepare authorization consistency solver
        authSolver = AuthorizationConsistencySolver(msSystem)

        # Return solver
        return authSolver


    # See if tests pass
    allPassed = True

    def conductTest(test, sol, expected):
        testResult = sol.solver.check()
        print(testResult)
        if testResult == sat:
            print(sol.solver.model())
        sol.clearSolver()
        if testResult == expected:
            print(f"TEST {test} passed!\n")
            return True
        else:
            print(f"TEST {test} failed!\n")
            return False

    # TEST 1 - Test adding data repository and user auth constraints
    s = prepareTest(1)
    s.addAtLeastOnePermittedRoleConstraints()
    s.addEndpointPermittedRoleConstraints()
    s.addDataEntityOperationConsistencyConstraints()
    allPassed = conductTest(1, s, sat) and allPassed

    # TEST 2 - Test adding all constraints and expected constraints
    s = prepareTest(2)
    s.addAtLeastOnePermittedRoleConstraints()
    s.addEndpointPermittedRoleConstraints()
    s.addDataEntityOperationConsistencyConstraints()
    allPassed = conductTest(2, s, sat) and allPassed

    if allPassed is True:
        print("All tests passed!\n")
    else:
        print("One or more tests failed!\n")
